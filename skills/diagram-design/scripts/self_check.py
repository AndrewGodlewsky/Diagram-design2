#!/usr/bin/env python3
"""Self-check a generated diagram HTML file, with no third-party deps.

Ships inside the skill so an installed agent can verify its own output:

    python3 <skill-dir>/scripts/self_check.py my-diagram.html

Checks accessible SVG names, static single-file safety, document completeness,
and basic geometry inside each SVG viewBox. All resources must be inline or
fragment references. Scripts, remote fonts, and animation are rejected.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from static_safety import normalize_css_escapes, read_local_utf8, safety_errors

VIEWBOX_TOLERANCE = 2.0
SVG_NUMBER = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
SVG_NUMBER_RE = re.compile(SVG_NUMBER)
SVG_PLAIN_NUMBER_RE = re.compile(rf"^\s*{SVG_NUMBER}\s*$")
TRANSLATE_RE = re.compile(rf"^\s*translate\(\s*({SVG_NUMBER})(?:[\s,]+({SVG_NUMBER}))?\s*\)\s*$")
REPLACEMENT_CHAR = "\ufffd"
# Container elements whose end tag HTML requires, so an unmatched count is real damage: a
# file that stops mid-element, a dropped </text>, a stray </span>. Void elements and the
# optional-end-tag elements (html, head, body, p, li, ...) stay out, so valid HTML cannot
# trip the count; the closing </html> of the generated shell is checked separately.
PAIRED_CONTAINER_TAGS = (
    "title",
    "desc",
    "div",
    "section",
    "main",
    "article",
    "header",
    "footer",
    "figure",
    "figcaption",
    "svg",
    "g",
    "defs",
    "pattern",
    "marker",
    "style",
    "script",
    "span",
    "text",
    "tspan",
)
# Their children are not painted where they are declared, or use another coordinate system.
UNPAINTED_TAGS = {
    "defs",
    "symbol",
    "marker",
    "pattern",
    "clippath",
    "mask",
    "foreignobject",
    "svg",
}
# CSS that can move, hide or clip an element, so its painted position is not its attributes.
UNSTATIC_CSS_PROPERTIES = {
    "transform",
    "translate",
    "rotate",
    "scale",
    "display",
    "visibility",
    "x",
    "y",
    "cx",
    "cy",
    "r",
    "rx",
    "ry",
    "width",
    "height",
}
UNSTATIC_CSS_PREFIXES = ("animation", "offset", "clip", "mask")
CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
CSS_KEYFRAMES_RE = re.compile(
    r"@(?:-[a-z]+-)?keyframes[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", re.IGNORECASE
)
CSS_RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}")
CSS_STRING_RE = re.compile(r"\"[^\"]*\"|'[^']*'")
CSS_PARENS_RE = re.compile(r"\([^()]*\)")
CSS_COMBINATOR_RE = re.compile(r"\s*[>+~]\s*|\s+")
CSS_TAG_RE = re.compile(r"^[a-zA-Z][\w-]*")
CSS_CLASS_RE = re.compile(r"\.([\w-]+)")
CSS_ID_RE = re.compile(r"#([\w-]+)")
CSS_ATTRIBUTE_RE = re.compile(r"\[\s*([\w:-]+)")
GEOMETRY_ATTRS = {
    "rect": ("x", "y", "width", "height"),
    "line": ("x1", "y1", "x2", "y2"),
    "circle": ("cx", "cy", "r"),
    "ellipse": ("cx", "cy", "rx", "ry"),
    "polygon": ("points",),
    "polyline": ("points",),
    "text": ("x", "y"),
}


class DiagramParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.styles: list[str] = []
        self.svgs: list[dict[str, object]] = []
        self.ids: Counter[str] = Counter()
        self._svg_depth = 0
        self._current_svg: dict[str, object] | None = None
        self._capture: str | None = None
        self._in_style = False
        self._element_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        normalized_attrs = [(key.casefold(), value or "") for key, value in attrs]
        data: dict[str, str] = {}
        for key, value in normalized_attrs:
            data.setdefault(key, value)
        if data.get("id"):
            self.ids[data["id"]] += 1
        if tag == "style":
            self._in_style = True
        self._element_stack.append(tag)
        if tag == "svg" and self._svg_depth == 0:
            self._svg_depth = 1
            self._current_svg = {"attrs": data, "first": None, "title": {}, "desc": {}}
            self.svgs.append(self._current_svg)
            return
        if self._svg_depth:
            self._svg_depth += 1
            assert self._current_svg is not None
            if self._svg_depth == 2 and self._current_svg["first"] is None:
                self._current_svg["first"] = tag
            if self._svg_depth == 2 and tag in {"title", "desc"}:
                self._current_svg[tag] = {"attrs": data, "text": ""}
                self._capture = tag

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if tag == "style":
            self._in_style = False
        if self._svg_depth:
            if tag in {"title", "desc"}:
                self._capture = None
            self._svg_depth -= 1
            if self._svg_depth == 0:
                self._current_svg = None
        for index in range(len(self._element_stack) - 1, -1, -1):
            if self._element_stack[index] == tag:
                del self._element_stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self.styles.append(data)
        if self._capture and self._current_svg:
            node = self._current_svg[self._capture]
            assert isinstance(node, dict)
            node["text"] = str(node.get("text", "")) + data


class SvgExtent:
    def __init__(self, attrs: dict[str, str]) -> None:
        self.attrs = attrs
        self.points: list[tuple[float, float, str]] = []


def svg_length(attrs: dict[str, str], name: str, default: float | None = None) -> float | None:
    value = attrs.get(name)
    if value is None:
        return default
    return float(value) if SVG_PLAIN_NUMBER_RE.match(value) else None


def painted_points(tag: str, attrs: dict[str, str]) -> list[tuple[float, float]]:
    if tag == "rect":
        x, y = svg_length(attrs, "x", 0.0), svg_length(attrs, "y", 0.0)
        width, height = svg_length(attrs, "width"), svg_length(attrs, "height")
        if x is None or y is None or width is None or height is None:
            return []
        if width <= 0 or height <= 0:
            return []
        return [(x, y), (x + width, y + height)]
    if tag == "line":
        ends = [
            (svg_length(attrs, "x1", 0.0), svg_length(attrs, "y1", 0.0)),
            (svg_length(attrs, "x2", 0.0), svg_length(attrs, "y2", 0.0)),
        ]
        return [(x, y) for x, y in ends if x is not None and y is not None]
    if tag in {"circle", "ellipse"}:
        cx, cy = svg_length(attrs, "cx", 0.0), svg_length(attrs, "cy", 0.0)
        rx = svg_length(attrs, "r" if tag == "circle" else "rx")
        ry = svg_length(attrs, "r" if tag == "circle" else "ry")
        if cx is None or cy is None or rx is None or ry is None:
            return []
        if rx <= 0 or ry <= 0:
            return []
        return [(cx - rx, cy - ry), (cx + rx, cy + ry)]
    if tag in {"polygon", "polyline"}:
        numbers = [float(value) for value in SVG_NUMBER_RE.findall(attrs.get("points", ""))]
        return list(zip(numbers[0::2], numbers[1::2]))
    if tag == "text":
        x, y = svg_length(attrs, "x"), svg_length(attrs, "y")
        return [] if x is None or y is None else [(x, y)]
    return []


def declares_unstatic_css(declarations: str) -> bool:
    for declaration in declarations.split(";"):
        name = declaration.split(":", 1)[0].strip().casefold()
        if name in UNSTATIC_CSS_PROPERTIES or name.startswith(UNSTATIC_CSS_PREFIXES):
            return True
    return False


def selector_subjects(selector: str) -> list[tuple[str, set[str], set[str], set[str]]]:
    """Tag, classes, IDs and attribute names a selector's last compound requires."""
    subjects = []
    for alternative in CSS_PARENS_RE.sub("", CSS_STRING_RE.sub("", selector)).split(","):
        parts = [part for part in CSS_COMBINATOR_RE.split(alternative.strip()) if part]
        if not parts:
            continue
        compound = parts[-1].split("::", 1)[0]
        tag = CSS_TAG_RE.match(compound)
        subjects.append((
            tag.group(0).casefold() if tag else "",
            set(CSS_CLASS_RE.findall(compound)),
            set(CSS_ID_RE.findall(compound)),
            {name.casefold() for name in CSS_ATTRIBUTE_RE.findall(compound)},
        ))
    return subjects


def unstatic_css_subjects(source: str) -> list[tuple[str, set[str], set[str], set[str]]]:
    """Selector subjects of stylesheet rules that move, hide or clip what they match.

    Matching keeps only the last compound and drops pseudo-classes, so it can match more
    elements than the browser does. That only skips checks; it never adds a finding.
    """
    styles = re.findall(r"<style\b[^>]*>(.*?)</style\s*>", source, re.IGNORECASE | re.DOTALL)
    sheet = CSS_KEYFRAMES_RE.sub("", CSS_COMMENT_RE.sub("", "\n".join(styles)))
    subjects = []
    for selector, declarations in CSS_RULE_RE.findall(sheet):
        if declares_unstatic_css(declarations):
            subjects.extend(selector_subjects(selector))
    return subjects


def matches_subject(
    tag: str, attrs: dict[str, str], subject: tuple[str, set[str], set[str], set[str]]
) -> bool:
    subject_tag, classes, ids, attribute_names = subject
    if subject_tag not in {"", "*", tag}:
        return False
    if not classes <= set(attrs.get("class", "").split()):
        return False
    if not ids <= {attrs.get("id", "")}:
        return False
    return attribute_names <= set(attrs)


def child_offset(
    tag: str,
    attrs: dict[str, str],
    parent: tuple[float, float] | None,
    css_subjects: list[tuple[str, set[str], set[str], set[str]]],
) -> tuple[float, float] | None:
    """Offset of an element in viewBox units, or None when its paint is not static."""
    if parent is None or tag in UNPAINTED_TAGS:
        return None
    if declares_unstatic_css(attrs.get("style", "")):
        return None
    if attrs.get("display", "").strip().casefold() == "none":
        return None
    if attrs.get("visibility", "").strip().casefold() in {"hidden", "collapse"}:
        return None
    if attrs.get("clip-path", "none").strip().casefold() != "none":
        return None
    if attrs.get("mask", "none").strip().casefold() != "none":
        return None
    if any(matches_subject(tag, attrs, subject) for subject in css_subjects):
        return None
    transform = attrs.get("transform")
    if transform is None:
        return parent
    match = TRANSLATE_RE.match(transform)
    if match is None:
        return None
    return parent[0] + float(match.group(1)), parent[1] + float(match.group(2) or 0)


class ViewBoxParser(HTMLParser):
    def __init__(self, css_subjects: list[tuple[str, set[str], set[str], set[str]]]) -> None:
        super().__init__(convert_charrefs=True)
        self.svgs: list[SvgExtent] = []
        self._css_subjects = css_subjects
        self._frames: list[tuple[str, tuple[float, float] | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        data = {key.casefold(): value or "" for key, value in attrs}
        if not self._frames:
            if tag == "svg":
                self.svgs.append(SvgExtent(data))
                self._frames.append((tag, (0.0, 0.0)))
            return
        offset = child_offset(tag, data, self._frames[-1][1], self._css_subjects)
        self._frames.append((tag, offset))
        if offset is None:
            return
        label = " ".join(
            [f"<{tag}"]
            + [f'{name}="{data[name]}"' for name in GEOMETRY_ATTRS.get(tag, ()) if name in data]
        ) + ">"
        for x, y in painted_points(tag, data):
            self.svgs[-1].points.append((x + offset[0], y + offset[1], label))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        for index in range(len(self._frames) - 1, -1, -1):
            if self._frames[index][0] == tag:
                del self._frames[index:]
                return


def parsed_document(source: str) -> DiagramParser:
    parser = DiagramParser()
    parser.feed(source)
    parser.close()
    return parser


class BalanceParser(HTMLParser):
    """Counts start and end tags as parsed, so attribute values and CDATA stay opaque.

    Reading the raw source with a regular expression instead would count tag-like text
    inside a quoted attribute or a stylesheet as markup, and report an imbalance the
    document does not have. A self-closing tag arrives as both a start and an end tag,
    so it balances itself.

    Titles and text areas are RCDATA: `<title>Using <span> labels</title>` is literal
    text, not a span element. `HTMLParser` only separates RCDATA from markup from
    Python 3.13 on, so on the versions the skill supports the inner tag arrives here as
    a real one; this class ignores markup until the matching end tag instead.
    """

    RCDATA_ELEMENTS = ("title", "textarea")

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.opens: Counter[str] = Counter()
        self.closes: Counter[str] = Counter()
        self.rcdata = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.rcdata:
            return
        self.opens[tag] += 1
        if tag in self.RCDATA_ELEMENTS:
            self.rcdata = tag

    def handle_endtag(self, tag: str) -> None:
        if self.rcdata:
            if tag == self.rcdata:
                self.rcdata = ""
                self.closes[tag] += 1
            return
        self.closes[tag] += 1


def ends_with_shell_close(source: str) -> bool:
    """True when the last markup in the document is `</html>`.

    HTML allows comments and whitespace after the `</html>` end tag, so stripping only
    whitespace would reject valid files; a document that really stopped early has no
    closing tag left once trailing comments are removed.
    """
    tail = source.rstrip()
    while True:
        start = tail.rfind("<!--")
        if start < 0:
            break
        end = tail.find("-->", start + 4)
        if end < 0 or tail[end + 3 :].strip():
            break
        tail = tail[:start].rstrip()
    return re.search(r"</html\s*>\Z", tail, re.IGNORECASE) is not None


def check_document_completeness(source: str, errors: list[str]) -> None:
    """Reject a document that is not whole: truncation, mojibake, unbalanced markup.

    The other checks read a document's contents; none of them notices that the document
    stopped early. A generated file that was cut off mid-write still satisfies the
    accessible-SVG contract for the part that survived, so this check reads the shape of
    the whole file instead.
    """
    if not ends_with_shell_close(source):
        errors.append("document does not end with </html>; the file looks truncated")

    replacements = source.count(REPLACEMENT_CHAR)
    if replacements:
        line = source[: source.index(REPLACEMENT_CHAR)].count("\n") + 1
        errors.append(
            f"contains {replacements} U+FFFD replacement character(s), first on line {line}:"
            " the file has mojibake or a truncated multi-byte character"
        )

    parser = BalanceParser()
    parser.feed(source)
    parser.close()
    if parser.rcdata:
        # Everything after an unterminated RCDATA element is text, so the tag counts
        # below describe the damage rather than the cause; report the cause alone.
        errors.append(
            f"<{parser.rcdata}> is never closed; the rest of the document reads as its text"
        )
        return
    for tag in PAIRED_CONTAINER_TAGS:
        opens, closes = parser.opens[tag], parser.closes[tag]
        if opens != closes:
            errors.append(
                f"<{tag}> opens {opens} time(s) and closes {closes} time(s);"
                " the document is not balanced"
            )


def check_svgs(parser: DiagramParser, errors: list[str]) -> None:
    checkable = [
        svg
        for svg in parser.svgs
        if isinstance(svg["attrs"], dict)
        and str(svg["attrs"].get("aria-hidden", "")).casefold() != "true"
    ]
    if not checkable:
        errors.append("diagram file needs at least one accessible (non-aria-hidden) SVG")
    for number, svg in enumerate(checkable, 1):
        attrs = svg["attrs"]
        assert isinstance(attrs, dict)
        if attrs.get("role") != "img":
            errors.append(f"svg {number} needs role=img")
        labelled = attrs.get("aria-labelledby", "").split()
        title = svg["title"]
        desc = svg["desc"]
        assert isinstance(title, dict) and isinstance(desc, dict)
        title_attrs = title.get("attrs", {})
        desc_attrs = desc.get("attrs", {})
        assert isinstance(title_attrs, dict) and isinstance(desc_attrs, dict)
        if svg["first"] != "title":
            errors.append(f"svg {number} title must be its first child")
        if not str(title.get("text", "")).strip() or not str(desc.get("text", "")).strip():
            errors.append(f"svg {number} needs non-empty title and desc")
        title_id = title_attrs.get("id", "")
        desc_id = desc_attrs.get("id", "")
        if title_id in {"", "title"} or desc_id in {"", "desc"}:
            errors.append(f"svg {number} title/desc IDs must be diagram-prefixed, never bare")
        for naming_id in dict.fromkeys((title_id, desc_id)):
            if parser.ids[naming_id] > 1:
                errors.append(f"duplicate accessible SVG naming ID {naming_id!r}")
        if labelled != [title_id, desc_id]:
            errors.append(f"svg {number} aria-labelledby must name title then desc")


def check_viewbox(source: str, errors: list[str]) -> None:
    parser = ViewBoxParser(unstatic_css_subjects(source))
    parser.feed(source)
    parser.close()
    checkable = [
        svg for svg in parser.svgs if svg.attrs.get("aria-hidden", "").casefold() != "true"
    ]
    for number, svg in enumerate(checkable, 1):
        box = [float(value) for value in SVG_NUMBER_RE.findall(svg.attrs.get("viewbox", ""))]
        if len(box) != 4 or box[2] <= 0 or box[3] <= 0:
            continue
        left, top, width, height = box
        worst: dict[str, tuple[float, str]] = {}
        for x, y, label in svg.points:
            for side, overshoot in (
                ("left", left - x),
                ("top", top - y),
                ("right", x - (left + width)),
                ("bottom", y - (top + height)),
            ):
                if overshoot > VIEWBOX_TOLERANCE and overshoot > worst.get(side, (0.0, ""))[0]:
                    worst[side] = (overshoot, label)
        for side, (overshoot, label) in worst.items():
            errors.append(
                f"svg {number}: {label} paints {overshoot:g}px past the viewBox {side} edge "
                "and is clipped; grow the viewBox or move the content inside it"
            )


def verify(path: Path, offline: bool = False) -> list[str]:
    source = read_local_utf8(path)
    parser = parsed_document(source)
    errors = safety_errors(source)
    check_document_completeness(source, errors)
    check_svgs(parser, errors)
    check_viewbox(source, errors)
    return errors


def main() -> int:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("files", nargs="+", type=Path)
    argument_parser.add_argument(
        "--offline",
        action="store_true",
        help="compatibility alias; all output is always checked as local and static",
    )
    args = argument_parser.parse_args()
    failed = False
    for path in args.files:
        try:
            errors = verify(path, offline=args.offline)
        except (OSError, ValueError) as exc:
            errors = [str(exc)]
        if errors:
            failed = True
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"OK {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
