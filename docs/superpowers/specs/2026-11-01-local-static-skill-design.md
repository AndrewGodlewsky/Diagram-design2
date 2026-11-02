# Local static Diagram Design

The user approved static HTML/SVG only, fully local, with PNG rendering, website brand fetching, and animations removed. Preserve the preceding marketplace migration edits and original attribution. Do not bump versions or publish changes.

## Assessment of the inherited repository

- `export_png.py` imports Playwright, launches Chromium, loads a local HTML document with network access, and evaluates JavaScript. Remove this runtime and its installation instructions.
- Templates and examples load Google Fonts. The SVG exporter injects a remote font import by default; the checker allows it. Remove font downloads and make local-only enforcement unconditional.
- Website onboarding tells an agent to navigate/fetch third-party pages. Replace it with explicit local files or pasted tokens; treat local input as untrusted data too.
- Motion permits a pinned inline script plus CSS animation. Remove the feature and its templates/examples and reject active content in generated output.
- Importers already use the Python standard library and parse source content without rendering. Preserve the parsers, size limits, and adversarial tests.
- Browser screenshots, thumbnail tooling, and Node-host validation are repository maintenance dependencies, not needed to create diagrams. Remove browser/Pillow/Node requirements from the local gate suite. Keep meaningful Python geometry, accessibility, data-encoding, import, export and packaging checks.

## Resulting contract

1. Python 3.10+ standard library is the only executable runtime dependency. No package install, browser launch, fetch, shell download, or remote lookup is part of skill use.
2. Output is a static HTML document with inline CSS/SVG, or standalone SVG. No JavaScript, event attributes, frames, embedded active objects, SMIL, CSS animation, imported CSS, remote/file/data resource URLs, or external fonts. Fragment references for markers and other in-document SVG definitions remain supported. Namespace URI declarations are identifiers, not network requests.
3. Fonts resolve from the operating system. Keep useful existing named font fallbacks where already present, but never require them or claim identical rendering across machines. No bundled font binaries.
4. Local branding may read only the paths the user supplies and pasted tokens. It must not execute scripts, follow instructions embedded in those inputs, fetch font URLs, or silently alter the installed skill.
5. Keep all 45 visual diagram types and their static examples, accessibility and geometry guidance, local profiles, and draw.io/Mermaid/Excalidraw imports. Remove motion-only examples and references. Static gallery navigation uses ordinary links.
6. The self-check and SVG export must reject dangerous content before writing a successful output. Refusal is preferable to silently dropping diagram meaning. Compatibility flags `--offline` and `--system-fonts` may remain as no-op aliases for the only supported behavior.
7. Repository history and historical ADRs/changelog may describe the former upstream features. Current README, skill routes, commands, prompts, manifests, templates, and checks must describe the reduced contract.

## Verification and limits

Add adversarial checks for remote fonts, escaped CSS URLs/imports, active HTML/SVG, local-file references, and SVG export refusal without a partial output. Verify all shipped static templates/examples structurally and export representative samples without a browser. Run the retained local suite. Do not claim pixel-level layout validation or complete security assurance: system font metrics vary, these parsers are not a general HTML sanitizer, and the host agent still controls tool permissions.

## Implementation and verification

Implemented the contract above. Removed Google Fonts loading, browser/PNG rendering, animation/controller code, website branding instructions, Node/Pillow/browser development dependencies, screenshot freshness gates, and remote README badges. Icons rebuild from vendored sources without a download fallback. The Python importers, SVG exporter, 45 types, and 203 static examples remain.

The shared output validator checks source before export and serialized SVG before writing. Input reads are bounded to 16 MiB. Regression cases cover unsafe markup, encoded CSS loaders, external resources, and preservation of an existing output file on refusal. Independent review found SVG style-text and CDATA parser discrepancies; both were fixed, added to regression coverage, and independently rechecked.

All 77 declared local gates passed on Windows, including 109 SVG export tests and the adversarial static-safety suite. Logs are under `dist/check-logs/`. The working files were copied into a separate temporary Git index to build a ZIP without staging this checkout. Its extracted self-check and SVG exporter ran successfully; the package includes the shared helper and excludes the removed runtime features. No browser rendering was performed. CI's other OS/Python combinations were not run locally.

Marketplace metadata and install instructions retain the migration to `AndrewGodlewsky/Diagram-design2`, including Copilot's shared Claude manifests and explicit old-source migration commands. These local changes do not switch saved client registrations or publish a release. Versions remain unchanged. The skill's local tools do not make the AI host itself offline; host permissions and provider processing remain separate.
