from __future__ import annotations

"""
Optional ESCET command-line validation pre-check.

This module does not implement ESCET. It delegates syntactic/semantic CIF
validation to an external ESCET command when available.

Usage strategy:
- pass a command template with --escet-cmd, or
- set ESCET_CIF_CHECK_CMD in the environment.

The command template may contain:
- {cif}: input CIF path as provided
- {cif_abs}: absolute input CIF path

Example:
    ESCET_CIF_CHECK_CMD='cif2cif {cif_abs} /tmp/validated.cif'

If no command is configured, the validation step is reported as skipped rather
than silently ignored.
"""

from dataclasses import asdict, dataclass
import os
from pathlib import Path
import shlex
import subprocess
from typing import Any


def _ensure_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


@dataclass
class EscetValidationResult:
    source_path: str
    status: str  # "passed", "failed", "skipped"
    command: list[str] | None = None
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.status in {"passed", "skipped"}

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_text(self) -> str:
        lines = [
            "ESCET validation pre-check",
            f"source: {self.source_path}",
            f"status: {self.status}",
        ]

        if self.command is not None:
            lines.append("command: " + " ".join(shlex.quote(part) for part in self.command))
        if self.returncode is not None:
            lines.append(f"returncode: {self.returncode}")
        reason = _ensure_text(self.reason)
        stdout = _ensure_text(self.stdout)
        stderr = _ensure_text(self.stderr)

        if reason:
            lines.append(f"reason: {reason}")
        if stdout.strip():
            lines.append("stdout:")
            lines.append(stdout.strip())
        if stderr.strip():
            lines.append("stderr:")
            lines.append(stderr.strip())

        return "\n".join(_ensure_text(line) for line in lines)


def _command_from_template(command_template: str, cif_path: Path) -> list[str]:
    rendered = command_template.format(
        cif=str(cif_path),
        cif_abs=str(cif_path.resolve()),
    )
    return shlex.split(rendered)


def validate_with_escet(
    cif_path: str | Path,
    command_template: str | None = None,
    timeout: int = 60,
    required: bool = False,
) -> EscetValidationResult:
    cif_path = Path(cif_path)

    configured_command = command_template or os.environ.get("ESCET_CIF_CHECK_CMD")
    if not configured_command:
        result = EscetValidationResult(
            source_path=str(cif_path),
            status="skipped",
            reason="no ESCET command configured; set ESCET_CIF_CHECK_CMD or pass --escet-cmd",
        )
        if required:
            result.status = "failed"
            result.reason = "ESCET validation is required but no command was configured"
        return result

    command = _command_from_template(configured_command, cif_path)

    # If the template did not include the CIF placeholder, append it.
    if "{cif" not in configured_command:
        command.append(str(cif_path))

    try:
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return EscetValidationResult(
            source_path=str(cif_path),
            status="failed" if required else "skipped",
            command=command,
            reason=f"ESCET command not found: {exc}",
        )
    except subprocess.TimeoutExpired as exc:
        return EscetValidationResult(
            source_path=str(cif_path),
            status="failed",
            command=command,
            stdout=_ensure_text(exc.stdout),
            stderr=_ensure_text(exc.stderr),
            reason=f"ESCET validation timed out after {timeout} seconds",
        )

    return EscetValidationResult(
        source_path=str(cif_path),
        status="passed" if completed.returncode == 0 else "failed",
        command=command,
        returncode=completed.returncode,
        stdout=_ensure_text(completed.stdout),
        stderr=_ensure_text(completed.stderr),
        reason=None if completed.returncode == 0 else "ESCET command returned a non-zero exit code",
    )


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("cif")
    parser.add_argument("--cmd", default=None)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--required", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = validate_with_escet(
        args.cif,
        command_template=args.cmd,
        timeout=args.timeout,
        required=args.required,
    )

    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(result.to_text())

    if result.status == "failed":
        raise SystemExit(1)
