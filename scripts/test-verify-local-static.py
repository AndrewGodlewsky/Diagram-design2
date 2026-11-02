#!/usr/bin/env python3
"""Regression checks for package resource and dependency boundaries."""
import importlib.util
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("local_static", Path(__file__).with_name("verify-local-static.py"))
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        skill = root / "skills/diagram-design-local"
        (skill / "assets").mkdir(parents=True)
        (skill / "scripts").mkdir()
        example = skill / "assets/example-demo.html"
        safe = '<!doctype html><html><head><style>svg {fill: var(--ink)}</style></head><body><svg xmlns="http://www.w3.org/2000/svg"><path fill="url(#gradient)"/></svg></body></html>'
        example.write_text(safe, encoding="utf-8")
        assert not verify.verify(root), verify.verify(root)
        for bad in ('<script>alert(1)</script>', '<link rel="stylesheet" href="https://fonts.googleapis.com/css2">',
                    '<img src="../secret.png">', '<svg><animate attributeName="x"/></svg>',
                    '<meta http-equiv="refresh" content="0;url=https://example.com">'):
            example.write_text(safe.replace('</body>', bad + '</body>'), encoding="utf-8")
            assert verify.verify(root), bad
        example.write_text(safe, encoding="utf-8")
        runtime = skill / "scripts/demo.py"
        for bad in ('import socket', 'from urllib.request import urlopen', 'import playwright', '__import__("socket")'):
            runtime.write_text(bad, encoding="utf-8")
            assert verify.verify(root), bad
        runtime.write_text('from urllib.parse import unquote\nimport json\n', encoding="utf-8")
        assert not verify.verify(root), verify.verify(root)
        gallery = skill / "assets/index.html"
        gallery.write_text('<a href="example-demo.html">Demo</a>', encoding="utf-8")
        assert not verify.verify(root), verify.verify(root)
        for target in ('https://example.com', '../secret.html', 'example-missing.html'):
            gallery.write_text(f'<a href="{target}">Demo</a>', encoding="utf-8")
            assert verify.verify(root), target
    print("OK: local-static package boundary adversarial cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
