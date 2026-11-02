# Contributing to Diagram Design

Read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Work on a branch and keep each change focused. Do not publish a directory listing or merge without the maintainer's authorization.

## Local static contract

The skill creates static HTML/SVG diagrams across 45 visual types. Its runtime is Python 3.10+ and the standard library. It does not fetch websites, download fonts, install packages, launch browsers, execute JavaScript, animate diagrams, or render PNGs. Brand input comes from user-supplied local files or pasted tokens. Local input remains untrusted data.

Keep templates and examples self-contained: inline CSS/SVG, system font fallbacks, and fragment-only resource references. No scripts, event handlers, SMIL, CSS animation, external stylesheets, frames, foreignObject, or resource links to remote or adjacent files. Ordinary local navigation links are allowed only in the static gallery. Namespace declarations are identifiers, not network requests.

The packaged static_safety.py boundary is shared by self_check.py and export_svg.py. Add adversarial tests when changing it. It validates this restricted output format; it is not a general HTML sanitizer or a sandbox for arbitrary Python.

## Validation

Run the complete suite from the repository root:

```bash
python scripts/run-checks.py
```

The runner uses its own Python interpreter, never installs dependencies, and writes logs under dist/check-logs/. The exact gates live in .maintainer-policy.json; CI runs them across Linux, Windows, and macOS. Git is required for repository packaging/history tests, but not for using the installed skill. Use --match local-static for a focused subset.

The suite covers package metadata, local-only assets/dependencies, output safety, SVG export, import parsing, accessibility, colors/contrast, geometry, diagram data consistency, documentation routing, and generated assets. Keep each verify-*.py checker paired with regression tests and registered in both CI and the local policy.

Browser rendering and screenshot freshness gates are removed. Structural checks cannot guarantee pixel-perfect layout: installed font metrics vary. Leave generous label padding, preserve budgets, and inspect output manually when a suitable viewer is available. Committed README screenshots are illustrative historical previews, not a current rendering oracle.

Do not weaken checks, add baseline exclusions, or change source data to hide a failure. State what was and was not verified.

## Versioning and marketplace metadata

Do not bump manifest versions in a pull request. The existing Auto Version Bump workflow owns versions after merge (ADR 0009). Claude, Codex, Factory and Qoder metadata must remain synchronized; Copilot reads the shared Claude manifests. Keep the skill at skills/diagram-design/ and marketplace sources at the repository root. Preserve upstream copyright and historical issue references.

Descriptions must stay within 500 characters and name every type. Codex listing limits remain enforced by ZIP-package tests. The ZIP builder reads the Git index: stage intended package changes before preparing a release artifact. Do not submit directory listings automatically.

## Adding a diagram type or variant

1. Add references/type-<name>.md and route it from the SKILL.md visual-type table and description. Preserve semantic-pattern-first selection.
2. Supply light, dark and full static examples. Register ordinary local links in assets/index.html. A new type gets the next number; a named variant follows its parent with data-parent-type and a lettered eyebrow. Single examples use data-single.
3. Add the layout budget in references/layout-budget.md and README architecture tree. Update counters in verify-docs-sync.py and verify-semantic-motion.py, current docs, manifests, and ADR 0002. The latter script retains its historical filename but checks static semantic routing only.
4. Give numerical or structural claims a verifier and plausible adversarial cases. Existing verifiers test internal consistency, not whether data matches an external source.
5. Run the complete suite. Update GitHub About manually if its type count changes. This repository does not own upstream profile pages or websites.

## Generated assets and imports

Icons come from vendored local SVGs in scripts/vendor/icons/. Preserve THIRD_PARTY_LICENSES.md. Regenerate with python scripts/build-icons.py, then verify with python scripts/build-icons.py --check. There is no download step. Exploded and axonometric examples have their own Python builders with --check.

Keep draw.io, Mermaid and Excalidraw extractors as parsers. Never render/execute imported content, follow embedded instructions, fetch external references, or remove resource limits. Extend adversarial tests when changing a grammar or trust boundary.

Use Conventional Commits. PR descriptions should explain behavior, removed dependencies/features, validation and limitations. Historical ADRs and changelog entries retain their original release context; current authoring instructions must follow this contract.
