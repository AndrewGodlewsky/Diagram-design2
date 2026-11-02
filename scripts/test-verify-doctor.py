#!/usr/bin/env python3
"""Local diagnostics require package integrity, never a browser or network probe."""
import contextlib
import importlib.util
import io
import sys
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("doctor", Path(__file__).with_name("verify-doctor.py"))
doctor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = doctor
spec.loader.exec_module(doctor)


def main():
    assert doctor.check_python_runtime().status == doctor.PASS
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        assert doctor.check_expected_scripts(root).status == doctor.FAIL
        (root / "SKILL.md").write_text("# Skill", encoding="utf-8")
        (root / "scripts").mkdir()
        for name in doctor.EXPECTED_SCRIPTS:
            (root / "scripts" / name).write_text("", encoding="utf-8")
        assert doctor.check_expected_scripts(root).status == doctor.PASS
        assert doctor.check_routing_surfaces(root).status == doctor.PASS
        for name in doctor.EXPECTED_SCRIPTS:
            path = root / "scripts" / name
            path.unlink()
            assert doctor.check_expected_scripts(root).status == doctor.FAIL, name
            path.write_text("", encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            assert doctor.run_doctor(root, root, True, True) == 0
        assert '"status": "PASS"' in output.getvalue()
        assert 'Playwright' not in output.getvalue()
        warn = doctor.CheckResult("fixture", doctor.WARN, "warning")
        assert doctor.summarize([warn], False)[2] == 0
        assert doctor.summarize([warn], True)[2] == 1
        fail = doctor.CheckResult("fixture", doctor.FAIL, "failure")
        assert doctor.summarize([fail], False)[2] == 1
    print("OK: local-only doctor checks packaged files, diagnostics, and failure status")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
