from __future__ import annotations

import importlib
import sys
from pathlib import Path


def load_generated_factory(package_dir: str | Path):
    """
    Import factory.py from a generated package directory.

    This loader is generic: it does not know model-specific module names.
    """

    package_dir = Path(package_dir)
    parent = str(package_dir.parent.resolve())

    if parent not in sys.path:
        sys.path.insert(0, parent)

    importlib.invalidate_caches()
    return importlib.import_module(f"{package_dir.name}.factory")
