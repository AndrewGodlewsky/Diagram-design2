# Export to SVG

Convert a generated static HTML diagram into standalone `.svg` with the packaged helper. Export only when requested. HTML remains the editable source.

Source files are UTF-8 and limited to 16 MiB. Oversized or unsafe input is refused before output is written; an existing output is left intact.

## Trigger and scope

Use for `/diagram-design:export-diagram <html-file>` or a request to save as SVG. Export is diagram-only: the first top-level SVG with its accessible title and description. Headers, summary cards, and footers stay in HTML. PNG and animated output are unsupported.

## Procedure

Resolve the installed skill directory rather than assuming the current directory. With Python 3.10+:

```text
python3 scripts/self_check.py <html-file>
python3 scripts/export_svg.py <html-file> [<out.svg>] [--system-fonts]
```

Use `python` if that is the available interpreter. No third-party dependencies or browser are required. `--system-fonts` is a compatibility alias: every export uses installed fonts with generic fallbacks and no font import.

The helper checks static local-only content before writing. Refuse scripts, active HTML/SVG, CSS animation, external stylesheets, font resources, and non-fragment resource URLs. Report errors and stop; do not silently remove prohibited content, reimplement a rejected export, or present a partial file as successful.

Report the output path and size on success. Default output is the source basename with `.svg`; honor explicit destinations and never overwrite the HTML source.

## Preserved SVG details

- Valid finite `viewBox` with positive width and height and the SVG namespace; namespace declarations are identifiers, not fetches.
- `role="img"`, resolving `aria-labelledby`, and first-child `<title>` followed by `<desc>`.
- Diagram CSS and inherited body color/font family, scoped to the exported root. Page chrome and responsive wrapper rules are omitted.
- Defs IDs prefixed by source slug with matching local `url(#...)` and `href="#..."` references updated, preventing shared markers between inlined figures.
- XML-safe text and CSS, and supported presentation color normalization that preserves opacity and CSS/inherited paint.
- Generic font fallbacks. Metrics and downstream editor support vary; structural validation is not pixel-level verification.

The helper owns these transformations. Do not duplicate its parser in agent-written code.

## Sizing the export

Set `viewBox` with [output-spec.md](output-spec.md) before drawing. Slide and social presets are layout choices, not raster scales. Include a background rect inside SVG for an opaque export. Retain label padding for system-font variation.

## Edge cases

- Missing source: ask for the intended local file.
- Gallery (`assets/index.html`): ask which example.
- No SVG, invalid viewport, unsafe content, or read/write failure: report failure without presenting output as complete.
- Multiple diagram SVGs: identify the intended diagram first; the helper selects the first top-level SVG.
- Registry: follow [export-registry.md](export-registry.md). `--registry` alone emits JSON; combine with `--svg-only` for both.
