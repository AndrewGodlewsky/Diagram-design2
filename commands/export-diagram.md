---
description: Export a static diagram HTML file to standalone SVG
argument-hint: <html-file> [--svg-only] [--output=<path>] [--registry]
allowed-tools:
  - Read
  - Write
  - Bash
---

Locate `diagram-design-local` from its advertised `SKILL.md` path. Read the skill and its `references/export.md`, then run packaged `scripts/export_svg.py`. Do not assume the current directory is the install. Export local HTML at `$1` to SVG; default destination is its basename with `.svg`. `--output` selects the destination base. `--svg-only` supports explicit composition with registry export.

Full argument string: `$ARGUMENTS`

For `--registry`, follow `references/export-registry.md`. Alone it emits only JSON; combine with `--svg-only` for both. Refuse missing source, gallery input, absent SVG, unsafe content, and unsupported flags. PNG/scale flags are unsupported. Never fetch resources, install dependencies, launch a browser, or silently remove rejected content. Report successful output paths and sizes.
