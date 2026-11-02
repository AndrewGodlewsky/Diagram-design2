#!/usr/bin/env python3
"""Regression tests for icon normalization and missing local sources."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "scripts" / "build-icons.py"


def load_build_module():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("diagram_design_build_icons", BUILD)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load build-icons.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    build_icons = load_build_module()
    svg = '<svg viewBox="0 0 32 32"><path fill="#123456" d="M0 0h32v32H0z"/></svg>'
    normalized = build_icons.normalize_devicon(svg)
    if 'viewBox="0 0 32 32"' not in normalized:
        raise AssertionError(f"source viewBox was not preserved: {normalized}")
    if 'fill="#123456"' in normalized:
        raise AssertionError("source fill escaped currentColor normalization")
    if 'fill="currentColor"' not in normalized:
        raise AssertionError("normalized icon does not inherit currentColor")
    print("PASS: Devicon normalization preserves non-128 source viewBoxes")
    missing = build_icons.VENDOR_DIR / "tabler" / "missing-test-icon.svg"
    with patch.object(build_icons, "vendor_path", return_value=missing), \
            patch.object(Path, "read_text", side_effect=FileNotFoundError(str(missing))), \
            patch.object(Path, "write_text") as write:
        try:
            build_icons.build()
        except FileNotFoundError as exc:
            if "Missing vendored icon" not in str(exc) or str(missing) not in str(exc):
                raise AssertionError(f"missing source has no actionable diagnostic: {exc}")
        else:
            raise AssertionError("missing vendored SVG did not fail")
        for args in ([str(BUILD)], [str(BUILD), "--check"]):
            diagnostic = io.StringIO()
            with patch.object(sys, "argv", args), contextlib.redirect_stderr(diagnostic):
                if build_icons.main() != 1:
                    raise AssertionError("missing source must fail both build and --check")
            if "network fetching is disabled" not in diagnostic.getvalue():
                raise AssertionError("missing source must explain the local-only contract")
        write.assert_not_called()
    print("PASS: missing vendored SVG fails without writing output in either mode")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
