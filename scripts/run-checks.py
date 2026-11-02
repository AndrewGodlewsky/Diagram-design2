#!/usr/bin/env python3
"""Run the repository's declared local gates with the active Python interpreter."""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--match", default="", help="Run only commands containing this text.")
    args = parser.parse_args()
    policy = json.loads((ROOT / ".maintainer-policy.json").read_text(encoding="utf-8"))
    commands = [c for c in policy["gates"]["local_commands"] if args.match in c]
    if not commands:
        parser.error("no matching checks")
    logs = ROOT / "dist/check-logs"
    logs.mkdir(parents=True, exist_ok=True)
    failures = []
    for index, command in enumerate(commands, 1):
        output = []
        for part in command.split(" && "):
            argv = shlex.split(part)
            if argv[0] in {"python", "python3"}:
                argv[0] = sys.executable
            result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
            output.append(result.stdout + result.stderr)
            if result.returncode:
                failures.append(command)
                break
        log = logs / f"{index:02d}-{Path(shlex.split(command)[1]).stem}.log"
        log.write_text("\n".join(output), encoding="utf-8")
        print(f"{'FAIL' if result.returncode else 'PASS'} {command}", flush=True)
        if result.returncode:
            print(f"  {log}", flush=True)
    print(f"{len(commands) - len(failures)}/{len(commands)} checks passed")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
