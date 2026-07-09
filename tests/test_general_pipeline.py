from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.auto_builder import build_engine_from_generated_package, run_engine_if_possible
from pipeline.feature_analyzer import analyze_file
from pipeline.python_generator_general import generate_general_from_cif
from pipeline.translation_manifest import build_manifest, write_manifest
from pipeline.escet_validator import validate_with_escet


def test_grid_cif_is_fully_generated_with_algebraic_greenhouse(tmp_path):
    cif = ROOT / "examples" / "Grid.cif"
    out = tmp_path / "generated_grid"

    report = generate_general_from_cif(cif, out)

    assert report.supported is True
    assert set(report.dynamic_automata) == {"Nodes", "LAI", "Biomass"}
    assert report.algebraic_input_automata == ["Greenhouse_template"]
    assert report.instance_counts["Greenhouse_template"] == 1
    assert report.instance_counts["Nodes"] == 1600
    assert report.instance_counts["LAI"] == 1600
    assert report.instance_counts["Biomass"] == 1600

    assert (out / "greenhouse.py").exists()
    assert (out / "nodes.py").exists()
    assert (out / "lai.py").exists()
    assert (out / "biomass.py").exists()
    assert (out / "factory.py").exists()

    sys.path.insert(0, str(tmp_path))
    import importlib
    factory = importlib.import_module("generated_grid.factory")
    greenhouse = importlib.import_module("generated_grid.greenhouse")

    assert factory.INSTANCE_COUNTS["Nodes"] == 1600
    assert factory.INSTANCE_COUNTS["LAI"] == 1600
    assert factory.INSTANCE_COUNTS["Biomass"] == 1600
    assert "Greenhouse_template" in factory.INPUT_REGISTRY
    assert greenhouse.LIST_SIZE == 1600


def test_grid_cif_runs_through_auto_builder(tmp_path):
    cif = ROOT / "examples" / "Grid.cif"
    out = tmp_path / "generated_grid_run"
    generate_general_from_cif(cif, out)

    build = build_engine_from_generated_package(out, cif, limit=3, hours=48)
    result = run_engine_if_possible(build)

    assert result["mode"] == "step-driven"
    assert build.execution_order[:3] == ["Nodes_0", "Nodes_1", "Nodes_2"]
    assert len(build.input_modules) == 1
    assert len(build.dynamic_modules) == 9

    results = build.engine.get_results()
    assert results["Nodes_0_N"][-1] > 6.0
    assert results["LAI_0_lai"][-1] > 0.017
    assert results["Biomass_0_w"][-1] > 0.0


def test_plain_coffee_machine_cif_generates_and_runs(tmp_path):
    cif = ROOT / "examples" / "coffee_machine.cif"
    out = tmp_path / "generated_coffee"

    report = generate_general_from_cif(cif, out)
    assert report.supported is True
    assert report.plain_automata == ["CoffeeMachine"]
    assert report.dynamic_automata == ["CoffeeMachine"]

    build = build_engine_from_generated_package(out, cif)
    result = run_engine_if_possible(
        build,
        events=["input_coffee", "heat_water", "add_water", "deliver_cup"],
    )

    assert result["mode"] == "event-driven"
    locations = [item["variables"]["location"] for item in result["events"]]
    assert locations == [
        "WaitingOrder",
        "GrindingCoffee",
        "HeatingWater",
        "ExtractingCoffee",
        "WaitingOrder",
    ]


def test_analyzer_reports_supported_subset_for_grid():
    report = analyze_file(ROOT / "examples" / "Grid.cif")
    assert report.supported is True
    assert "algebraic list input modules" in report.supported_features
    assert report.unsupported_features == []


def test_translation_manifest_validates_grid_generation(tmp_path):
    cif = ROOT / "examples" / "Grid.cif"
    out = tmp_path / "generated_grid_manifest"

    report = generate_general_from_cif(cif, out)
    report_dir = tmp_path / 'reports' / 'Grid'
    manifest = write_manifest(cif, out, report=report, report_dir=report_dir)

    assert manifest.valid is True
    assert manifest.generated_instance_counts["Nodes"] == 1600
    assert manifest.generated_instance_counts["LAI"] == 1600
    assert manifest.generated_instance_counts["Biomass"] == 1600
    assert manifest.expected_instance_counts["Greenhouse_template"] == 1
    assert manifest.input_instance_names["Greenhouse_template"] == "Greenhouse"
    assert manifest.resolved_bindings_count == 14400

    assert (report_dir / 'translation_manifest.json').exists()
    assert (report_dir / 'translation_manifest.json').exists()
    assert (report_dir / 'translation_manifest.md').exists()


def test_translation_manifest_validates_plain_automaton(tmp_path):
    cif = ROOT / "examples" / "coffee_machine.cif"
    out = tmp_path / "generated_coffee_manifest"

    report = generate_general_from_cif(cif, out)
    manifest = build_manifest(cif, out, report=report)

    assert manifest.valid is True
    assert manifest.generated_instance_counts["CoffeeMachine"] == 1
    assert manifest.expected_instance_counts["CoffeeMachine"] == 1
    assert manifest.resolved_bindings_count == 0


def test_diagnostics_rejects_explicit_sync(tmp_path):
    cif = tmp_path / "sync_example.cif"
    cif.write_text(
        """
event e;

automaton A:
    location L:
        initial;
        edge e goto L;
end

sync e;
"""
    )

    report = analyze_file(cif)

    assert report.supported is False
    assert any("SYNC" in item["code"] for item in report.diagnostics)
    assert any("synchronization" in item for item in report.unsupported_features)


def test_diagnostics_warns_on_controllable_events(tmp_path):
    cif = tmp_path / "controllable_example.cif"
    cif.write_text(
        """
controllable event start;

automaton A:
    location Idle:
        initial;
        edge start goto Running;
    location Running:
        edge start goto Running;
end
"""
    )

    report = analyze_file(cif)

    assert report.supported is True
    assert any("CONTROLLABLE_UNCONTROLLABLE" in item["code"] for item in report.diagnostics)
    assert any("runtime event-trigger policy" in item for item in report.warnings)


def test_diagnostics_file_is_available():
    subset_doc = ROOT / "docs" / "SUPPORTED_CIF_SUBSET.md"
    assert subset_doc.exists()
    text = subset_doc.read_text()
    assert "Grid.cif" in text
    assert "resolved bindings: 14400" in text


def test_generated_grid_package_runner_is_created_and_runs(tmp_path):
    import subprocess

    cif = ROOT / "examples" / "Grid.cif"
    out = tmp_path / "generated_grid_runner"

    proc = subprocess.run(
        [
            "python3",
            str(ROOT / "scripts" / "cif_to_python.py"),
            str(cif),
            "--output",
            str(out),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stdout
    assert (out / "source_model.cif").exists()
    assert (out / "run_generated_model.py").exists()
    assert (out / "README_GENERATED_MODEL.md").exists()

    run_proc = subprocess.run(
        [
            "python3",
            str(out / "run_generated_model.py"),
            "--limit",
            "2",
            "--hours",
            "24",
        ],
        cwd=out,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert run_proc.returncode == 0, run_proc.stdout
    assert "Generated package run summary" in run_proc.stdout
    assert "mode: step-driven" in run_proc.stdout
    assert "dynamic modules instantiated: 6" in run_proc.stdout


def test_generated_coffee_package_runner_is_created_and_runs(tmp_path):
    import subprocess

    cif = ROOT / "examples" / "coffee_machine.cif"
    out = tmp_path / "generated_coffee_runner"

    proc = subprocess.run(
        [
            "python3",
            str(ROOT / "scripts" / "cif_to_python.py"),
            str(cif),
            "--output",
            str(out),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stdout
    assert (out / "source_model.cif").exists()
    assert (out / "run_generated_model.py").exists()

    run_proc = subprocess.run(
        [
            "python3",
            str(out / "run_generated_model.py"),
            "--events",
            "input_coffee",
            "heat_water",
            "add_water",
            "deliver_cup",
        ],
        cwd=out,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert run_proc.returncode == 0, run_proc.stdout
    assert "mode: event-driven" in run_proc.stdout
    assert "deliver_cup: fired=True location=WaitingOrder" in run_proc.stdout


def test_escet_validator_accepts_successful_external_command(tmp_path):
    cif = tmp_path / "valid.cif"
    cif.write_text("event e;")

    result = validate_with_escet(
        cif,
        command_template="python3 -c 'import sys; sys.exit(0)'",
        required=True,
    )

    assert result.status == "passed"
    assert result.returncode == 0


def test_escet_validator_reports_failing_external_command(tmp_path):
    cif = tmp_path / "invalid.cif"
    cif.write_text("event e;")

    result = validate_with_escet(
        cif,
        command_template="python3 -c 'import sys; sys.exit(7)'",
        required=True,
    )

    assert result.status == "failed"
    assert result.returncode == 7


def test_escet_validator_skips_when_not_configured(tmp_path, monkeypatch):
    # Keep the test independent from the developer/user shell environment.
    # On machines where ESCET_CIF_CHECK_CMD is exported for real validation runs,
    # validate_with_escet would otherwise execute that command and report "passed".
    monkeypatch.delenv("ESCET_CIF_CHECK_CMD", raising=False)

    cif = tmp_path / "model.cif"
    cif.write_text("event e;")

    result = validate_with_escet(cif)

    assert result.status == "skipped"
    assert result.ok is True



def test_generated_factory_has_no_case_specific_helpers(tmp_path):
    cif = tmp_path / "mini_template_names.cif"
    cif.write_text(
        """
event e;

automaton def Nodes():
    location A:
        initial;
        edge e goto A;
end

automaton def LAI():
    location A:
        initial;
        edge e goto A;
end

automaton def Biomass():
    location A:
        initial;
        edge e goto A;
end

n0: Nodes();
l0: LAI();
b0: Biomass();
"""
    )
    out = tmp_path / "generated_no_case_helpers"

    generate_general_from_cif(cif, out)

    factory_text = (out / "factory.py").read_text()
    assert "create_tomgro_modules" not in factory_text
    assert "NODES_INSTANCE_COUNT" not in factory_text
    assert "LAI_INSTANCE_COUNT" not in factory_text
    assert "BIOMASS_INSTANCE_COUNT" not in factory_text


def test_interactive_bash_pipeline_can_generate_without_escet_or_simulation(tmp_path):
    import subprocess

    cif = ROOT / "examples" / "coffee_machine.cif"
    out = ROOT / "out" / "generated" / cif.stem
    report_dir = ROOT / "out" / "reports" / cif.stem
    shutil.rmtree(out, ignore_errors=True)

    proc = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts" / "run_pipeline.sh"),
            str(cif),
        ],
        input="n\nn\n",
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stdout
    assert "ESCET validation skipped" in proc.stdout
    assert "Generation completed" in proc.stdout
    assert "Simulation skipped" in proc.stdout
    assert (out / "factory.py").exists()
    assert (report_dir / 'translation_manifest.json').exists()
    assert (report_dir / 'translation_manifest.md').exists()


def test_interactive_bash_pipeline_can_run_event_simulation(tmp_path):
    import subprocess

    cif = ROOT / "examples" / "coffee_machine.cif"
    out = ROOT / "out" / "generated" / cif.stem
    report_dir = ROOT / "out" / "reports" / cif.stem
    history_csv = ROOT / "out" / "outputs" / cif.stem / "results" / "history.csv"
    shutil.rmtree(out, ignore_errors=True)
    if history_csv.exists():
        history_csv.unlink()

    proc = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts" / "run_pipeline.sh"),
            str(cif),
        ],
        input="n\ny\nevent\n\ninput_coffee heat_water add_water deliver_cup\n\n",
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stdout
    assert "Step 3/3 - Event-driven simulation" in proc.stdout
    assert "History CSV output: out/outputs/coffee_machine/results/history.csv" in proc.stdout
    assert "deliver_cup: fired=True location=WaitingOrder" in proc.stdout
    assert history_csv.exists()


def test_interactive_bash_pipeline_can_use_escet_command(tmp_path):
    import subprocess

    cif = ROOT / "examples" / "coffee_machine.cif"
    out = ROOT / "out" / "generated" / cif.stem
    shutil.rmtree(out, ignore_errors=True)

    proc = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts" / "run_pipeline.sh"),
            str(cif),
        ],
        input="y\n300\npython3 -c 'import sys; sys.exit(0)'\nn\n",
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stdout
    assert "ESCET validation pre-check" in proc.stdout
    assert "status: passed" in proc.stdout
    assert (out / "factory.py").exists()


def test_controllable_event_is_external_not_automatic(tmp_path):
    cif = tmp_path / "controllable_event.cif"
    cif.write_text(
        """
controllable go;

automaton A:
    location Idle:
        initial;
        edge go goto Running;
    location Running:
        edge go goto Running;
end
"""
    )
    out = tmp_path / "generated_controllable"
    generate_general_from_cif(cif, out)

    build = build_engine_from_generated_package(out, cif)
    module = build.engine.modules[build.execution_order[0]]

    assert module.get_variables()["location"] == "Idle"
    assert module.external_events() == ["go"]
    assert module.automatic_events() == []

    fired_by_step = module.step([])
    assert fired_by_step is False
    assert module.get_variables()["location"] == "Idle"

    fired_explicitly = module.fire("go")
    assert fired_explicitly is True
    assert module.get_variables()["location"] == "Running"


def test_uncontrollable_event_is_automatic_candidate(tmp_path):
    cif = tmp_path / "uncontrollable_event.cif"
    cif.write_text(
        """
uncontrollable tick;

automaton A:
    location Idle:
        initial;
        edge tick goto Running;
    location Running:
        edge tick goto Running;
end
"""
    )
    out = tmp_path / "generated_uncontrollable"
    generate_general_from_cif(cif, out)

    build = build_engine_from_generated_package(out, cif)
    module = build.engine.modules[build.execution_order[0]]

    assert module.get_variables()["location"] == "Idle"
    assert module.automatic_events() == ["tick"]

    fired_by_step = module.step([])
    assert fired_by_step is True
    assert module.get_variables()["location"] == "Running"


def test_plain_event_is_external_by_default(tmp_path):
    cif = tmp_path / "plain_event.cif"
    cif.write_text(
        """
event start;

automaton A:
    location Idle:
        initial;
        edge start goto Running;
    location Running:
        edge start goto Running;
end
"""
    )
    out = tmp_path / "generated_plain_event"
    generate_general_from_cif(cif, out)

    build = build_engine_from_generated_package(out, cif)
    module = build.engine.modules[build.execution_order[0]]

    assert module.event_info("start")["trigger"] == "external"
    assert module.step([]) is False
    assert module.get_variables()["location"] == "Idle"


def test_grid_events_are_marked_automatic_in_generated_metadata(tmp_path):
    cif = ROOT / "examples" / "Grid.cif"
    out = tmp_path / "generated_grid_event_metadata"
    generate_general_from_cif(cif, out)

    build = build_engine_from_generated_package(out, cif, limit=1, hours=24)
    nodes = build.engine.modules["Nodes_0"]
    biomass = build.engine.modules["Biomass_0"]

    assert nodes.event_info("day")["kind"] == "uncontrollable"
    assert nodes.event_info("day")["trigger"] == "automatic"
    assert biomass.event_info("hour")["trigger"] == "automatic"
    assert biomass.event_info("update")["trigger"] == "automatic"



def test_generated_runner_can_use_event_trace_csv(tmp_path):
    import subprocess

    cif = ROOT / "examples" / "coffee_machine.cif"
    events_csv = ROOT / "examples" / "coffee_machine_events.csv"
    out = tmp_path / "generated_coffee_event_trace"

    gen_proc = subprocess.run(
        [
            "python3",
            str(ROOT / "scripts" / "cif_to_python.py"),
            str(cif),
            "--output",
            str(out),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert gen_proc.returncode == 0, gen_proc.stdout

    run_proc = subprocess.run(
        [
            "python3",
            str(out / "run_generated_model.py"),
            "--events-csv",
            str(events_csv),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert run_proc.returncode == 0, run_proc.stdout
    assert "mode: event-trace" in run_proc.stdout
    assert "deliver_cup: fired=True location=WaitingOrder" in run_proc.stdout


def test_generated_runner_can_use_data_trace_csv(tmp_path):
    import subprocess

    cif = ROOT / "examples" / "Grid.cif"
    data_csv = ROOT / "examples" / "grid_weather_input.csv"
    out = tmp_path / "generated_grid_data_trace"

    gen_proc = subprocess.run(
        [
            "python3",
            str(ROOT / "scripts" / "cif_to_python.py"),
            str(cif),
            "--output",
            str(out),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert gen_proc.returncode == 0, gen_proc.stdout

    run_proc = subprocess.run(
        [
            "python3",
            str(out / "run_generated_model.py"),
            "--input-csv",
            str(data_csv),
            "--limit",
            "2",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert run_proc.returncode == 0, run_proc.stdout
    assert "mode: step-driven" in run_proc.stdout
    assert "steps: 24" in run_proc.stdout
    assert "T_mean" in run_proc.stdout


def test_interactive_bash_pipeline_can_run_event_csv_simulation(tmp_path):
    import subprocess

    cif = ROOT / "examples" / "coffee_machine.cif"
    events_csv = ROOT / "examples" / "coffee_machine_events.csv"
    out = ROOT / "out" / "generated" / cif.stem
    history_csv = ROOT / "out" / "outputs" / cif.stem / "results" / "history.csv"
    shutil.rmtree(out, ignore_errors=True)
    if history_csv.exists():
        history_csv.unlink()

    proc = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts" / "run_pipeline.sh"),
            str(cif),
        ],
        input=f"n\ny\nevent\n{events_csv}\n\n",
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stdout
    assert "Step 3/3 - Event-trace simulation" in proc.stdout
    assert "History CSV output: out/outputs/coffee_machine/results/history.csv" in proc.stdout
    assert "deliver_cup: fired=True location=WaitingOrder" in proc.stdout
    assert history_csv.exists()


def test_interactive_bash_pipeline_can_run_data_csv_simulation(tmp_path):
    import subprocess

    cif = ROOT / "examples" / "Grid.cif"
    data_csv = ROOT / "examples" / "grid_weather_input.csv"
    out = ROOT / "out" / "generated" / cif.stem
    history_csv = ROOT / "out" / "outputs" / cif.stem / "results" / "history.csv"
    shutil.rmtree(out, ignore_errors=True)
    if history_csv.exists():
        history_csv.unlink()

    proc = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts" / "run_pipeline.sh"),
            str(cif),
        ],
        input=f"n\ny\nstep\n2\n24\n1\n{data_csv}\n\n",
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=160,
    )

    assert proc.returncode == 0, proc.stdout
    assert "Step 3/3 - Step-driven simulation" in proc.stdout
    assert "History CSV output: out/outputs/Grid/results/history.csv" in proc.stdout
    assert "mode: step-driven" in proc.stdout
    assert "steps: 24" in proc.stdout
    assert history_csv.exists()



def test_generated_runner_can_export_grid_history_csv(tmp_path):
    import csv
    import subprocess

    cif = ROOT / "examples" / "Grid.cif"
    data_csv = ROOT / "examples" / "grid_weather_input.csv"
    out = tmp_path / "generated_grid_history_export"
    history_csv = tmp_path / "grid_history.csv"

    gen_proc = subprocess.run(
        [
            "python3",
            str(ROOT / "scripts" / "cif_to_python.py"),
            str(cif),
            "--output",
            str(out),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert gen_proc.returncode == 0, gen_proc.stdout

    run_proc = subprocess.run(
        [
            "python3",
            str(out / "run_generated_model.py"),
            "--input-csv",
            str(data_csv),
            "--limit",
            "2",
            "--history-csv",
            str(history_csv),
            "--history-vars",
            "Nodes_0_N",
            "LAI_0_lai",
            "Biomass_0_w",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert run_proc.returncode == 0, run_proc.stdout
    assert history_csv.exists()

    rows = list(csv.reader(history_csv.open()))
    assert rows[0] == ["sample", "Biomass_0_w", "LAI_0_lai", "Nodes_0_N"]
    assert len(rows) > 2


def test_generated_runner_can_export_event_trace_history_csv(tmp_path):
    import csv
    import subprocess

    cif = ROOT / "examples" / "coffee_machine.cif"
    events_csv = ROOT / "examples" / "coffee_machine_events.csv"
    out = tmp_path / "generated_coffee_history_export"
    history_csv = tmp_path / "coffee_history.csv"

    gen_proc = subprocess.run(
        [
            "python3",
            str(ROOT / "scripts" / "cif_to_python.py"),
            str(cif),
            "--output",
            str(out),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert gen_proc.returncode == 0, gen_proc.stdout

    run_proc = subprocess.run(
        [
            "python3",
            str(out / "run_generated_model.py"),
            "--events-csv",
            str(events_csv),
            "--history-csv",
            str(history_csv),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert run_proc.returncode == 0, run_proc.stdout
    assert history_csv.exists()

    rows = list(csv.reader(history_csv.open()))
    assert rows[0] == ["sample", "CoffeeMachine_0_location"]
    assert rows[-1][-1] == "WaitingOrder"



def test_escet_behavior_comparison_script_with_sample_trace(tmp_path):
    import subprocess

    cif = ROOT / "examples" / "coffee_machine.cif"
    escet_trace = ROOT / "examples" / "coffee_machine_escet_trace_sample.csv"
    out = tmp_path / "generated_coffee_escet_comparison"
    comparison_out = tmp_path / "escet_comparison"

    gen_proc = subprocess.run(
        [
            "python3",
            str(ROOT / "scripts" / "cif_to_python.py"),
            str(cif),
            "--output",
            str(out),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert gen_proc.returncode == 0, gen_proc.stdout

    cmp_proc = subprocess.run(
        [
            "python3",
            str(ROOT / "validation" / "compare_with_escet_behavior.py"),
            "--cif",
            str(cif),
            "--generated-dir",
            str(out),
            "--events-csv",
            str(ROOT / "examples" / "coffee_machine_events.csv"),
            "--escet-trace",
            str(escet_trace),
            "--output-dir",
            str(comparison_out),
            "--var-map",
            "CoffeeMachine_0_location=CoffeeMachine_0_location",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )

    assert cmp_proc.returncode == 0, cmp_proc.stdout
    assert "status: pass" in cmp_proc.stdout

    report = comparison_out / "escet_vs_generated_behavior.md"
    assert report.exists()
    assert "PASS" in report.read_text()


def test_escet_behavior_comparison_docs_exist():
    doc = ROOT / "docs" / "ESCET_BEHAVIOR_COMPARISON.md"
    assert doc.exists()
    assert "ESCET trace" in doc.read_text()
    assert "behavior comparison" in doc.read_text()


def test_event_semantics_docs_exist():
    event_doc = ROOT / "docs" / "EVENT_SEMANTICS.md"
    matrix_doc = ROOT / "docs" / "CIF_SUPPORT_MATRIX.md"

    assert event_doc.exists()
    assert matrix_doc.exists()

    assert "controllable" in event_doc.read_text()
    assert "sync" in matrix_doc.read_text()
