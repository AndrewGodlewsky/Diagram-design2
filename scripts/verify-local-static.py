#!/usr/bin/env python3
"""Verify the installed package stays static, local, and standard-library-only."""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills/diagram-design-local/scripts"))
from static_safety import safety_errors

ALLOWED_MODULES = {
    "__future__", "argparse", "base64", "collections", "dataclasses", "html",
    "json", "math", "pathlib", "re", "struct", "sys", "typing", "zlib",
    "xml.etree", "xml.etree.ElementTree", "urllib.parse", "static_safety",
}
FORBIDDEN_FILES = ("scripts/export_png.py", "references/animation.md", "assets/template-motion.html")


def verify(root: Path) -> list[str]:
    skill = root / "skills/diagram-design-local"
    errors = []
    for relative in FORBIDDEN_FILES:
        if (skill / relative).exists():
            errors.append(f"removed runtime surface reintroduced: {relative}")
    for path in sorted((skill / "scripts").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            modules = [alias.name for alias in node.names] if isinstance(node, ast.Import) else (
                [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            for module in modules:
                if module not in ALLOWED_MODULES and not module.startswith("html."):
                    errors.append(f"{path.name}:{node.lineno}: runtime import {module!r} is outside the local parsing contract")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec", "__import__"}:
                errors.append(f"{path.name}:{node.lineno}: dynamic code execution is not allowed")
    for path in sorted((skill / "assets").glob("*.html")):
        source = path.read_text(encoding="utf-8")
        if path.name.endswith("-animated.html"):
            errors.append(f"motion-only example reintroduced: {path.name}")
        if path.name == "index.html":
            # The static catalog may navigate to shipped examples, but may not load
            # another document or resource automatically. Generated output may not.
            def navigation(match: re.Match[str]) -> str:
                target = match.group(2)
                if not re.fullmatch(r"(?:example-[a-z0-9-]+|icons)\.html", target) or not (path.parent / target).is_file():
                    errors.append(f"gallery navigation must target a shipped example: {target!r}")
                return "<a>"
            source = re.sub(r'<a\s+href=([\'"])(.*?)\1\s*>', navigation, source)
        errors.extend(f"{path.name}: {error}" for error in safety_errors(source))
    return errors


def main() -> int:
    errors = verify(ROOT)
    for error in errors:
        print(f"FAIL: {error}")
    if not errors:
        print("OK: shipped HTML is static/local and runtime Python uses only approved standard-library parsers")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
