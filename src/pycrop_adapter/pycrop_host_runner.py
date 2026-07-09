from __future__ import annotations

import argparse
import csv
import importlib
import json
import sys
from pathlib import Path
from typing import Iterable

SRC_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pipeline.path_defaults import resolve_generated_dir, require_generated_package, default_pycrop_dir, default_reports_dir
from pipeline.result_exports import export_history_csv, export_history_json, parse_history_variables

def _add_sys_path(path: Path) -> None:
    s = str(path.resolve())
    if s not in sys.path:
        sys.path.insert(0, s)


def _load_manifest(generated_dir: Path) -> dict:
    report_dir = default_reports_dir(generated_dir=generated_dir, project_root=ROOT_DIR)
    return json.loads((report_dir / 'translation_manifest.json').read_text())


def _package_name(generated_dir: Path) -> str:
    return generated_dir.name


def _read_input_csv(path: Path) -> dict[str, list[float]]:
    with path.open('r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        raise ValueError(f'Input CSV is empty: {path}')
    series: dict[str, list[float]] = {}
    for key in reader.fieldnames or []:
        if key is None or key == 'step':
            continue
        series[key] = [float(row[key]) for row in rows]
    return series


def _resolve_bindings(cif_path: Path, template_filter, limit_per_template: int | None):
    from pipeline.binding_resolver import resolve_bindings_from_file
    return resolve_bindings_from_file(cif_path, template_filter=template_filter, limit_per_template=limit_per_template)


def build_engine(args):
    generated_dir = require_generated_package(resolve_generated_dir(args.generated_dir, args.cif, ROOT_DIR), args.cif).resolve()
    generated_root = generated_dir.parent
    project_root = generated_root.parent.parent if len(generated_root.parents) > 1 else generated_root.parent
    _add_sys_path(generated_root)
    _add_sys_path(project_root)

    # Import the generated package first. This intentionally lets the generated
    # runtime use its lightweight internal base classes, after which we host the
    # instances inside the real PyCrop engine through adapters.
    manifest = _load_manifest(generated_dir)
    package_name = _package_name(generated_dir)
    factory = importlib.import_module(f'{package_name}.factory')

    if args.pycrop_root:
        pycrop_root = Path(args.pycrop_root).resolve()
        _add_sys_path(pycrop_root)
    else:
        raise ValueError('--pycrop-root is required for PyCrop hosting mode')

    from PyCrop.Implementations.Engines.SimulationEngine import SimulationEngine
    from pycrop_adapter.generated_events_input_module import GeneratedEventsCsvInputModule
    from pycrop_adapter.generated_input_adapter import GeneratedInputModulePyCropAdapter
    from pycrop_adapter.generated_module_adapter import GeneratedModulePyCropAdapter

    engine = SimulationEngine(args.engine_name)

    if args.events_csv:
        modules_by_template = factory.create_modules(limit_per_template=args.limit, granularity=args.event_granularity)
        adapters = []
        for modules in modules_by_template.values():
            for name, module in modules.items():
                adapters.append(
                    GeneratedModulePyCropAdapter(
                        module,
                        mode='event',
                        event_target=name,
                        allow_automatic_step=False,
                    )
                )
        engine.add_module(adapters)

        event_input = GeneratedEventsCsvInputModule(args.events_csv)
        event_input.read_input()
        engine.add_input_module(event_input)
        for adapter in adapters:
            engine.bindVariables(event_input.get_name(), 'events', adapter.get_name(), 'events')

        return engine, manifest

    if not args.input_csv:
        raise ValueError('Either --events-csv or --input-csv is required')

    input_series = _read_input_csv(Path(args.input_csv))
    input_modules = factory.create_input_modules(limit=args.limit, hours=args.hours, **input_series)
    input_adapters = [GeneratedInputModulePyCropAdapter(module) for module in input_modules.values()]
    engine.add_input_module(input_adapters)

    modules_by_template = factory.create_modules(limit_per_template=args.limit)
    module_adapters = []
    for modules in modules_by_template.values():
        for module in modules.values():
            module_adapters.append(GeneratedModulePyCropAdapter(module, mode='data'))
    engine.add_module(module_adapters)

    cif_path = Path(args.cif) if args.cif else generated_dir / 'source_model.cif'
    bindings = _resolve_bindings(cif_path, template_filter=manifest.get('dynamic_templates'), limit_per_template=args.limit)
    for binding in bindings:
        engine.bindVariables(binding.source_module, binding.source_variable, binding.target_module, binding.target_variable)

    # Fallback for remaining direct/global inputs that are not reconstructed by the
    # structural binding resolver, such as plain numeric parameters exposed by an
    # input adapter (e.g. T_in in Grid/TOMGRO).
    input_variable_index: dict[str, str] = {}
    for input_name, input_module in engine.inputs.items():
        for variable_name in input_module.get_variable_names():
            input_variable_index.setdefault(variable_name, input_name)

    for module_name, module in engine.modules.items():
        required_inputs = list(module.show_required_inputs())
        for input_name in required_inputs:
            if input_name in engine.input_bindings[module_name]:
                continue
            provider = input_variable_index.get(input_name)
            if provider is None:
                continue
            engine.bindVariables(provider, input_name, module_name, input_name)

    return engine, manifest


def summarize_results(results: dict, prefixes: list[str] | None = None) -> dict:
    if not prefixes:
        return {k: (v[-1] if isinstance(v, list) and v else v) for k, v in results.items()}
    summary = {}
    for key, value in results.items():
        if any(key.startswith(prefix) for prefix in prefixes):
            summary[key] = value[-1] if isinstance(value, list) and value else value
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description='Run generated CIF modules inside PyCrop via adapters.')
    parser.add_argument('--pycrop-root', help='Path to extracted PyCrop_restrict root that contains the PyCrop package.')
    parser.add_argument('--generated-dir', default=None, help='Generated package directory (default: out/generated/<CIF stem>)')
    parser.add_argument('--cif', default=None, help='Optional CIF path used to infer --generated-dir and for runtime binding reconstruction when omitted')
    parser.add_argument('--input-csv', help='Numeric scenario CSV for data-driven models')
    parser.add_argument('--events-csv', help='Event scenario CSV for event-driven models')
    parser.add_argument('--hours', type=int, default=6, help='Hours to simulate in data-driven mode')
    parser.add_argument('--seconds', type=int, default=6, help='Seconds/steps to simulate in event-driven mode')
    parser.add_argument('--limit', type=int, default=None, help='Optional per-template instance limit')
    parser.add_argument('--event-granularity', type=int, default=1, help='Granularity to assign to event-driven generated modules')
    parser.add_argument('--engine-name', default='PyCropGeneratedEngine')
    parser.add_argument('--output-json', help='Optional path to write a summary JSON (default location is out/outputs/<Model>/pycrop/summary.json when omitted but summary export is enabled programmatically)')
    parser.add_argument('--history-csv', help='Optional path to export PyCrop-hosted history as CSV')
    parser.add_argument('--history-json', help='Optional path to export PyCrop-hosted history as JSON')
    parser.add_argument('--history-vars', nargs='*', default=None, help='Optional variable filters for history export')
    args = parser.parse_args(argv)

    engine, manifest = build_engine(args)
    if args.events_csv:
        engine.run_till_timestep(args.seconds)
        prefixes = [name for name in engine.modules.keys()]
    else:
        engine.run_till_timestep(args.hours * 3600)
        prefixes = ['Nodes_', 'LAI_', 'Biomass_', 'Greenhouse_']

    results = engine.get_results()
    resolved_generated_dir = str(resolve_generated_dir(args.generated_dir, args.cif, ROOT_DIR))
    summary = {
        'engine_name': engine.get_name(),
        'generated_dir': resolved_generated_dir,
        'mode': 'event' if args.events_csv else 'data',
        'module_count': len(engine.modules),
        'input_module_count': len(engine.inputs),
        'manifest_dynamic_templates': manifest.get('dynamic_templates', []),
        'summary': summarize_results(results, prefixes=prefixes),
    }

    history = engine.get_results()
    history_vars = parse_history_variables(args.history_vars)
    if args.history_csv:
        export_history_csv(history, args.history_csv, variables=history_vars)
    if args.history_json:
        export_history_json(history, args.history_json, variables=history_vars)

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
