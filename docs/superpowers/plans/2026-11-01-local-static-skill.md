# Local Static Skill Implementation Plan

> For agentic workers: implement the scoped tasks and review their integration before completion.

**Goal:** Make diagram creation static and local using only Python's standard library.

**Architecture:** Keep the existing skill, local parsers, SVG exporter, and static diagram library. Delete browser rendering and motion features; enforce the output boundary in the packaged checker and exporter.

**Tech Stack:** Python 3.10+ standard library, static HTML/CSS/SVG, JSON and Markdown.

**Spec:** `docs/superpowers/specs/2026-11-01-local-static-skill-design.md`

## Global constraints

Preserve marketplace migration edits, all 45 visual types, import safety limits, and license. No version bump or publishing. No network, downloaded fonts, automated browser, or third-party runtime package in skill use.

## Review focus

Remote URLs disguised with CSS escapes; executable SVG retained by export; local file references leaking adjacent files; active examples reintroduced by generators; stale command/docs instructions telling an agent to install or fetch removed dependencies.

## Tasks

- [x] Packaged boundary: update `self_check.py` and `export_svg.py`; remove `export_png.py`; add/update meaningful adversarial tests and run the self-check/export test suites. Reject scripts, remote resources, file/data URLs, SMIL and CSS animation; preserve safe SVG styling and namespacing.
- [x] Authoring surfaces: update SKILL.md, references, commands/prompts, README/cookbook, privacy and listing claims for local fonts, local branding, HTML/SVG-only output and static operation. Remove motion-only reference files and routes; keep layout/type guidance.
- [x] Assets: remove webfont links from all assets, delete motion-only examples/template, make the gallery static, and update generators so they cannot reintroduce removed behavior. Run structure/geometry checks on the remaining examples.
- [x] Maintenance: retire browser/Pillow and Node tool dependencies, screenshot freshness and motion-only gates; synchronize CI and maintainer policy. Update docs checks to enforce the new contract rather than retired features. Keep unrelated pure-Python verification.
- [x] Integrate: audit shipped files for network/active content, run retained tests and sample SVG exports, review diff and document limitations and removed features.
