#!/usr/bin/env python3
"""Verify semantic-pattern routing for static diagrams.

Uses only the Python standard library and never executes example JavaScript.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills/diagram-design-local/SKILL.md"
GIT_ROOT = ROOT
PATTERNS = ROOT / "skills/diagram-design-local/references/semantic-patterns.md"
ADR_0002 = ROOT / "docs/adr/0002-semantic-patterns-do-not-expand-the-taxonomy.md"
MAX_SKILL_BYTES = 40_000
VISUAL_TYPE_COUNT = 45

PATTERN_NAMES = (
    "Fan-in queue / bottleneck",
    "Stage framework with semantic slots",
    "Unstructured input → structured artifact",
    "Paired policy-evaluation traces",
    "Secure paved road",
    "Governance / control catalog",
    "Compensating security layers",
    "Traceable block decomposition",
    "Lifecycle phase map",
)
PATTERN_FIELDS = (
    "Selection triggers:",
    "Required primitives:",
    "Complexity budget:",
    "Anti-patterns:",
    "Static representation:",
    "Nearest visual type:",
)
def section(markdown: str, heading: str, next_heading: str | None) -> str:
    start = markdown.find(heading)
    if start < 0:
        return ""
    end = markdown.find(next_heading, start + len(heading)) if next_heading else -1
    return markdown[start:] if end < 0 else markdown[start:end]


NUMBER_WORDS = (
    "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
    "fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty"
)

def verify_type_count_record() -> list[str]:
    """ADR 0002 is the authority for the visual-type count; the counter follows it.

    Every dated amendment is titled "the count is N" or "the pattern count is
    <n>", amendments are in date order, and the newest "the count is N" must name
    VISUAL_TYPE_COUNT, so a PR cannot move the counter without recording the
    admission.
    """
    errors: list[str] = []
    adr = ADR_0002.read_text(encoding="utf-8")
    # Find every bold paragraph that opens with a digit before judging its
    # form, so a malformed date cannot hide an amendment from the check.
    amendments = re.findall(
        r"^\*\*(\d[\d-]*\d)\s+\S+\s+(.+?)\.\*\*", adr, re.MULTILINE
    )
    dates: list[str] = []
    for date, _title in amendments:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            errors.append(f"ADR 0002 amendment date {date!r} is not a YYYY-MM-DD date")
            continue
        try:
            datetime.date(int(date[:4]), int(date[5:7]), int(date[8:]))
        except ValueError:
            errors.append(f"ADR 0002 amendment date {date!r} is not a real date")
            continue
        dates.append(date)
    counts: list[tuple[str, int]] = []
    for date, title in amendments:
        count = re.fullmatch(r"the count is (\d+)", title)
        if count:
            counts.append((date, int(count.group(1))))
        elif not re.fullmatch(rf"the pattern count is (?:\d+|{NUMBER_WORDS})", title):
            errors.append(
                f"ADR 0002 amendment dated {date} is titled {title!r}; title it "
                "'the count is N' (or 'the pattern count is N' for a semantic "
                "pattern) so the counters can be checked against it"
            )
    if dates != sorted(dates):
        errors.append(f"ADR 0002 amendments are not in date order: {', '.join(dates)}")
    if not counts:
        errors.append("ADR 0002 records no visual-type count amendment")
    elif counts[-1][1] != VISUAL_TYPE_COUNT:
        errors.append(
            f"ADR 0002's latest amendment records the visual-type count as {counts[-1][1]}, "
            f"but the counters say {VISUAL_TYPE_COUNT}; add an amendment titled "
            f"'the count is {VISUAL_TYPE_COUNT}' as the last entry, dated on or after "
            f"{max(dates) if dates else 'the newest amendment'}"
        )
    return errors


SKILL_PATH_IN_REPO = "skills/diagram-design-local/SKILL.md"


def skill_lf_pin_problem(root: Path) -> str | None:
    """Why the committed .gitattributes would not keep SKILL.md LF, or None.

    Git itself resolves the attributes (`git check-attr`), so every rule,
    glob, bracket expression, and later override counts exactly as git
    counts it. It runs in a scratch repository holding only the committed
    .gitattributes files on SKILL.md's path, with global and system config
    switched off and inherited GIT_* variables dropped, so neither a
    contributor's own attributes nor a hook's repository can stand in for the
    repository pin.
    """
    git = shutil.which("git")
    if git is None:
        return None
    parts = Path(SKILL_PATH_IN_REPO).parent.parts
    committed = [Path(*parts[:depth], ".gitattributes") for depth in range(len(parts) + 1)]
    with tempfile.TemporaryDirectory(prefix="skill-lf-pin-") as scratch:
        scratch_root = Path(scratch)
        # Drop inherited GIT_* variables: a hook's GIT_DIR or GIT_WORK_TREE would
        # otherwise point both commands at the caller's repository.
        env = {
            **{name: value for name, value in os.environ.items() if not name.startswith("GIT_")},
            # Paths that do not exist read as empty on every platform.
            "GIT_CONFIG_GLOBAL": str(scratch_root / "no-global-config"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "HOME": scratch,
            "XDG_CONFIG_HOME": scratch,
        }
        subprocess.run([git, "init", "-q", scratch], capture_output=True, env=env, check=True)
        for relative in committed:
            source = root / relative
            if source.is_file():
                target = scratch_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
        result = subprocess.run(
            [git, "-C", scratch, "-c", f"core.attributesFile={(scratch_root / 'no-attributes').as_posix()}",
             "check-attr", "text", "eol", "--", SKILL_PATH_IN_REPO],
            capture_output=True,
            text=True,
            env=env,
        )
    if result.returncode != 0:
        return f"git check-attr failed: {result.stderr.strip()}"
    values = dict(
        line.rsplit(": ", 2)[1:] for line in result.stdout.splitlines() if line.count(": ") >= 2
    )
    if values.get("text") not in ("set", "auto") or values.get("eol") != "lf":
        return (
            ".gitattributes must pin skills/diagram-design-local/SKILL.md to `text eol=lf` "
            f"so the byte cap measures the committed file (git resolves text={values.get('text')}, "
            f"eol={values.get('eol')})"
        )
    return None

def verify_markdown() -> list[str]:
    errors: list[str] = []
    # Measure the committed LF content. A checkout with core.autocrlf=true adds
    # one CR per line, which would otherwise fail the cap on Windows (#246).
    skill_bytes = SKILL.read_bytes().replace(b"\r\n", b"\n")
    skill = skill_bytes.decode("utf-8")
    patterns = PATTERNS.read_text(encoding="utf-8")

    if len(skill_bytes) > MAX_SKILL_BYTES:
        errors.append(
            f"SKILL.md exceeds {MAX_SKILL_BYTES} bytes: {len(skill_bytes)} bytes"
        )
    pin_problem = skill_lf_pin_problem(GIT_ROOT)
    if pin_problem:
        errors.append(pin_problem)
    if "Selection: semantic pattern, then visual type" not in skill:
        errors.append("SKILL.md must choose semantic pattern before visual type")
    router_position = skill.find("semantic-patterns.md")
    guide_heading = f"### Visual-type guide ({VISUAL_TYPE_COUNT})"
    guide_position = skill.find(guide_heading)
    if router_position < 0:
        errors.append("SKILL.md must link to semantic-patterns.md")
    if guide_position < 0:
        errors.append(
            f"SKILL.md must contain the {VISUAL_TYPE_COUNT}-row visual-type guide"
        )
    if router_position >= 0 and guide_position >= 0 and router_position > guide_position:
        errors.append("semantic-pattern router must precede the visual-type guide")

    visual_guide = section(skill, guide_heading, "Rules of thumb:")
    visual_rows = re.findall(r"^\|.*\[type-[^)]+\.md\]", visual_guide, re.MULTILINE)
    if len(visual_rows) != VISUAL_TYPE_COUNT:
        errors.append(
            f"visual-type guide must preserve {VISUAL_TYPE_COUNT} rows; found {len(visual_rows)}"
        )

    opening = next(
        (
            block
            for block in re.split(r"\n\s*\n", patterns)
            if block.strip() and not block.lstrip().startswith("#")
        ),
        "",
    )
    if f"the {VISUAL_TYPE_COUNT} visual types" not in opening:
        errors.append(
            f"semantic-patterns.md must name the {VISUAL_TYPE_COUNT} visual types in its "
            "opening paragraph, matching the counters"
        )

    for index, name in enumerate(PATTERN_NAMES, 1):
        if name not in skill:
            errors.append(f"SKILL.md does not route semantic pattern: {name}")
        next_heading = f"## {index + 1}." if index < len(PATTERN_NAMES) else "## Composition rules"
        block = section(patterns, f"## {index}. {name}", next_heading)
        if not block:
            errors.append(f"semantic-patterns.md is missing section {index}: {name}")
            continue
        for field in PATTERN_FIELDS:
            if f"**{field}**" not in block:
                errors.append(f"{name} is missing required field {field}")

    errors.extend(verify_type_count_record())
    return errors






def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown-only", action="store_true", help="Compatibility alias; only static documentation is checked.")
    parser.parse_args()
    errors = verify_markdown()
    for error in errors:
        print(f"FAIL: {error}")
    if not errors:
        print("OK: static semantic patterns, routing, type count and skill size")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
