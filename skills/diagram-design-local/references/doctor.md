# Environment doctor

Run read-only diagnostics for `/diagram-design-local:doctor`, `/diagram-design-local-doctor`, or a readiness request. Resolve the installation from its loaded skill path, not the current directory. Never install packages, launch a browser, fetch resources, or change files.

## Inputs

`--strict` treats warnings as failures; `--json` appends structured results.

## Required checks

1. **Python:** try `python3`, then `python`; unlaunchable commands and Windows Store aliases are not interpreters. Require a reported version >=3.10. Missing/older Python is `fail`; continue independent file checks.
2. **Packaged scripts:** require `scripts/drawio_extract.py`, `scripts/mermaid_extract.py`, `scripts/excalidraw_extract.py`, `scripts/export_svg.py`, and `scripts/self_check.py`. Run each with `--help` using the resolved interpreter, capturing errors. All use the standard library.
3. **Authoring files:** require `SKILL.md`, `references/style-guide.md`, `references/output-spec.md`, `references/export.md`, `references/profiles.md`, and `assets/template.html`, `assets/template-dark.html`, `assets/template-full.html`.
4. **Static sample:** run `scripts/self_check.py assets/template.html` from the resolved skill directory. Report the actual exit and diagnostic. This checks source structure, not rendered pixels.
5. **Routing:** verify skill links to imports, export, onboarding, profiles, and this reference resolve inside the installation. Missing commands/prompts are acceptable for a skill-only installation.
6. **Maintainer checkout only:** if `CONTRIBUTING.md` and `.maintainer-policy.json` exist above the skill, report that the retained repository gate suite is available. Installed skills do not require repository-only files.

## Report

Print a compact summary and `pass`, `warn`, or `fail` per check. Continue independent checks after failures. Include `Next actions` only for unresolved findings. Missing Python means executable checks are unverified, not passed.

With `--json`, append:

```json
{"status":"pass","checks":[{"name":"python","status":"pass","detail":"Python 3.11"}],"next_actions":[]}
```

Overall status is `fail` for failures, `warn` for warnings alone (`fail` under `--strict`), otherwise `pass`. Readiness is not an audit of host-agent permissions or a guarantee about arbitrary input.
