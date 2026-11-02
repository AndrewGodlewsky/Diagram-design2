# Diagram Design cookbook

Operator recipes for this repository. The design system still lives in [`skills/diagram-design/SKILL.md`](../skills/diagram-design/SKILL.md); this file is the runbook: what to say, which files to load, and which commands to run.

Use it from an **editable clone** (this checkout). Managed marketplace installs can still follow the recipes, but do not edit `references/style-guide.md` inside a package that updates will replace — save a [client profile](../skills/diagram-design/references/profiles.md) instead.

---

## Map

| I want to… | Jump |
|---|---|
| Wire this clone into Claude, Codex, Cursor, Cline, Kiro, OpenCode, or Copilot | [R0](#r0-editable-install) |
| Confirm Python and local SVG export | [R1](#r1-doctor) |
| Draw the first diagram in a real project | [R2](#r2-first-diagram-in-a-project) |
| Match a brand | [R3](#r3-onboard-a-skin) |
| Choose type / pattern / size without rereading the whole skill | [R4](#r4-selection-cheat-sheet) |
| Browse shipped examples | [R5](#r5-gallery-and-templates) |
| Redraw draw.io or Mermaid | [R6](#r6-import) |
| Hand off SVG | [R7](#r7-export) |
| Check a generated HTML file | [R8](#r8-taste-and-geometry-gates) |
| Paste a request to an agent | [R9](#r9-prompt-pack) |

---

## R0. Editable install

The canonical skill root is `skills/diagram-design/` (`SKILL.md` + `references/` + `assets/`). Point skill hosts at that inner directory. Pi and the repository's native marketplace packages are the exceptions because they already resolve the `skills/` directory from the repository root.

This repository does not duplicate `SKILL.md` into host-specific loader stubs. For an editable install, symlink or junction the canonical inner directory into one discovery root used by your host.

### Host matrix

| Host | How it finds the skill | What you do |
|---|---|---|
| **Claude Code** | Marketplace plugin, `~/.claude/skills/`, or project `.claude/skills/` | Use `/plugin install` for managed updates or link the inner skill for editable work. |
| **Codex** | Marketplace plugin or `~/.agents/skills/` | Use the marketplace for managed updates or link the inner skill for editable work. |
| **Cursor** | `~/.cursor/skills/`, `~/.agents/skills/`, project `.cursor/skills/`, or project `.agents/skills/` | Link the inner skill, then ask in Agent chat. |
| **Cline CLI / VS Code** | `~/.cline/skills/`, `~/.agents/skills/`, workspace `.cline/skills/`, or workspace `.agents/skills/` | Link the inner skill and enable it from the Skills view when needed. |
| **Kiro** | Workspace `.kiro/skills/` or global `~/.kiro/skills/` | Link the inner skill, or import its GitHub subdirectory URL; imported skills are copied and must be re-imported to update. |
| **OpenCode** | Project `.opencode/skills/` or global `~/.config/opencode/skills/` | Link or copy the inner skill; copied installs must be replaced to update. |
| **GitHub Copilot** | Marketplace plugin; project `.github/skills/`, `.agents/skills/`, or `.claude/skills/`; user `~/.copilot/skills/`, `~/.agents/skills/`, or `~/.claude/skills/` | Use the marketplace for managed updates or link the inner skill for editable work. |

Marketplace installs (Claude `/plugin`, `copilot plugin install`, `codex plugin add`, `droid plugin install`) stay the right path if you do **not** need to edit `style-guide.md` in-tree. Use profiles instead. For the hosts in the matrix that have no marketplace package, `npx skills add AndrewGodlewsky/Diagram-design2` does the same job in one command - it installs the inner skill into every root you select, symlinking them to one canonical copy by default and copying independently under `--copy`. That install is standalone: it belongs to the CLI rather than to your checkout or to any marketplace, so it does not follow marketplace updates automatically. Refresh it with `npx skills update diagram-design`.

### Unix (user-global inner skill)

```bash
git clone https://github.com/AndrewGodlewsky/Diagram-design2.git ~/code/diagram-design
DIAGRAM_SKILL=~/code/diagram-design/skills/diagram-design
mkdir -p ~/.claude/skills ~/.cursor/skills ~/.agents/skills ~/.cline/skills \
  ~/.kiro/skills ~/.config/opencode/skills ~/.copilot/skills
ln -s "$DIAGRAM_SKILL" ~/.claude/skills/diagram-design
ln -s "$DIAGRAM_SKILL" ~/.cursor/skills/diagram-design
ln -s "$DIAGRAM_SKILL" ~/.agents/skills/diagram-design
ln -s "$DIAGRAM_SKILL" ~/.cline/skills/diagram-design
ln -s "$DIAGRAM_SKILL" ~/.kiro/skills/diagram-design
ln -s "$DIAGRAM_SKILL" ~/.config/opencode/skills/diagram-design
ln -s "$DIAGRAM_SKILL" ~/.copilot/skills/diagram-design
```

Create only the destinations for the hosts you use. When a host scans both its native root and `.agents/skills/`, choose one so it does not discover the same skill twice.

### Windows (directory junction — not a file symlink)

```powershell
$src = "E:\diagram-design\skills\diagram-design"
foreach ($t in @(
  "$env:USERPROFILE\.claude\skills\diagram-design",
  "$env:USERPROFILE\.cursor\skills\diagram-design",
  "$env:USERPROFILE\.agents\skills\diagram-design",
  "$env:USERPROFILE\.cline\skills\diagram-design",
  "$env:USERPROFILE\.kiro\skills\diagram-design",
  "$env:USERPROFILE\.config\opencode\skills\diagram-design",
  "$env:USERPROFILE\.copilot\skills\diagram-design"
)) {
  $parent = Split-Path $t -Parent
  if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
  if (-not (Test-Path $t)) { cmd /c mklink /J "$t" "$src" }
}
```

Replace `E:\diagram-design` with your clone path. If a junction already exists, leave it; do not copy the skill over a managed plugin folder.

Pi still registers the **repo root**: `pi install <clone-path>`.

---

## R1. Doctor

Ask `run diagram-design doctor` or `/diagram-design:doctor` / `/doctor`. The [doctor procedure](../skills/diagram-design/references/doctor.md) checks Python 3.10+, packaged scripts, authoring files, and a static sample without installing packages or launching a browser. On Windows use the working `python` or `python3` interpreter rather than a Store alias.

---

## R2. First diagram in a project

Work in the **project that will own the HTML**, not inside `skills/diagram-design/assets/` unless you are contributing an example.

1. **Resolve local style** ([SKILL.md §0](../skills/diagram-design/SKILL.md)): use supplied session tokens, a selected local profile, or shipped defaults. Read profiles directly; never alter the installed guide.
2. **Confirm before drawing** ([SKILL.md §3](../skills/diagram-design/SKILL.md)): visual type, optional semantic pattern, size preset, and what the complexity budget will cut.
3. **Load** the matching `references/type-*.md` before writing SVG. If a semantic pattern applies, load [`semantic-patterns.md`](../skills/diagram-design/references/semantic-patterns.md) first.
4. **Write** a self-contained HTML file in the project (for example `docs/diagrams/<name>.html`). Do not silently overwrite gallery examples.
5. **Run** the pre-output checklist ([SKILL.md §9](../skills/diagram-design/SKILL.md)). Orthogonal connectors, 4px grid, ≤9 nodes unless you split, accent on ≤2 focals.

Marker file at the project root, entire file:

```text
profile: <slug>
```

See [`profiles.md`](../skills/diagram-design/references/profiles.md). Profiles live in `~/.diagram-design/profiles/`, not in this clone.

---

## R3. Onboard a skin

Full flow: [`onboarding.md`](../skills/diagram-design/references/onboarding.md).

Say one of:

- `Extract diagram-design tokens from the local design-system folder <path>`
- `Use these tokens: paper … ink … accent …` (manual)
- `Proceed with the default skin` (optionally write `profile: default` with consent)

Use the effective guide in session, or save a named external profile and select it with the project marker when requested. Never write branding into the installed package.

---

## R4. Selection cheat sheet

Use the current type selection table. Open [SKILL.md §3](../skills/diagram-design/SKILL.md) and pick one layout grammar.

**Behavior first** (then nearest type):

| If the story is… | Pattern → type |
|---|---|
| Fan-in, queues, bottlenecks | Fan-in queue → Data flow |
| Repeated stage slots | Stage framework → Process |
| Messy input becomes a durable artifact | Unstructured → structured → Data flow |
| Two policy traces, first divergence | Paired traces → Flowchart |
| Trust boundaries / paved road | Secure paved road → Architecture |
| Controls by enforcement layer | Governance catalog → Layer stack |
| Compensating defenses, residual risk | Compensating layers → Layer stack |

**Hard stops:** if a table or paragraph is clearer, do not draw. If you are over the [complexity budget](../skills/diagram-design/SKILL.md) (9 nodes / 12 arrows as the default ceiling), split overview + detail.

**Size** ([output-spec.md](../skills/diagram-design/references/output-spec.md)): `doc-inline` for docs, `slide-16x9` for decks, `social-og` for cards, `fit` for Figma SVG. Size changes type ramp, not just viewBox.


---

## R5. Gallery and templates

The [local gallery](../skills/diagram-design/assets/index.html) links to every static example. You can view it in your preferred local viewer; authoring does not require opening it.

Copy a scaffold, then replace the SVG:

```bash
cp skills/diagram-design/assets/template.html my-diagram.html
cp skills/diagram-design/assets/template-full.html my-diagram.html
```

Shipped examples are `assets/example-<type>.html` plus `-dark` and `-full` variants. Treat them as specimens, not scratch files.

---

## R6. Import

Load [`import-drawio.md`](../skills/diagram-design/references/import-drawio.md), [`import-mermaid.md`](../skills/diagram-design/references/import-mermaid.md), or [`import-excalidraw.md`](../skills/diagram-design/references/import-excalidraw.md) and set the four dials **before** redrawing ([output-spec.md](../skills/diagram-design/references/output-spec.md)):

| Dial | Typical values |
|---|---|
| Format | `html` · `svg` |
| Size | `doc-inline` · `slide-16x9` · `social-og` · `fit` · … |
| Detail | `faithful` · `balanced` · `simplified` |
| Audience | `engineer` · `mixed` · `executive` |

Slash forms (Claude): `/diagram-design:import-drawio <file>`, `/diagram-design:import-mermaid <file-or-md>`, and `/diagram-design:import-excalidraw <file>`. Always report a **fidelity ledger** (merged, collapsed, dropped). Source coordinates, source palette, Mermaid auto-layout, and Excalidraw hand-drawn geometry do not carry over.

Extractors in this checkout: `skills/diagram-design/scripts/drawio_extract.py`, `mermaid_extract.py`, `excalidraw_extract.py`.

---

## R7. Export

Export only when requested. Follow [export.md](../skills/diagram-design/references/export.md). SVG export keeps the diagram, scoped CSS, accessible name, and local definitions. Fonts use installed faces with generic fallbacks. It requires no browser or third-party package.

```text
/diagram-design:export-diagram path/to/diagram.html
python skills/diagram-design/scripts/export_svg.py path/to/diagram.html
```

`--registry` alone exports block metadata JSON; add `--svg-only` for both outputs.

---

## R8. Taste and geometry gates

After generating HTML in this clone (examples or a file you are contributing):

```bash
python skills/diagram-design/scripts/self_check.py path/to/diagram.html
python scripts/lint-skin.py path/to/diagram.html
python scripts/verify-geometry.py path/to/diagram.html
```

Full contributor gates: [CONTRIBUTING.md](../CONTRIBUTING.md). Docs/routing: `python scripts/verify-docs-sync.py`.

---

## R9. Prompt pack

Copy and fill. Keep one type, one size, one destination.

**Architecture (docs):**

> Draw an architecture diagram of [system]. Nodes: [list ≤9]. Focal: [1–2]. Size `doc-inline`, format HTML. Use the diagram-design skill. Confirm type and cuts before drawing. Save to `[path].html`.

**Deck:**

> Redraw `[file].drawio` for a 16:9 slide, detail `simplified`, audience `executive`, format SVG.

**Mermaid in a README:**

> Import every Mermaid block in `[file].md`, size `doc-wide`, detail `balanced`, audience `mixed`. Report the fidelity ledger.

**Brand, then diagram:**

> Read brand tokens from `[local-style-file]`. Using those tokens, save profile `[slug]` and write `.diagram-design` with `profile: [slug]`. Then draw [type] of [topic].

**Do not:**

> Make it look like Mermaid / add shadows / coral every box / diagonal connectors / more than nine nodes in one figure.

---

## Pointers

| Topic | File |
|---|---|
| Philosophy, types, checklist | [`SKILL.md`](../skills/diagram-design/SKILL.md) |
| Tokens | [`style-guide.md`](../skills/diagram-design/references/style-guide.md) |
| Settled design decisions | [`docs/adr/`](adr/) |
| Maintainer validation | [`CONTRIBUTING.md`](../CONTRIBUTING.md) |
