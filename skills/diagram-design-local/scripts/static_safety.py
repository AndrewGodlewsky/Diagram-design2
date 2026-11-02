"""Conservative, standard-library-only safety checks for static diagram source.

This rejects unsupported active/resource syntax; it is not an HTML sanitizer.
Both the source and the serialized SVG must pass before export can succeed.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

MAX_INPUT_BYTES = 16 * 1024 * 1024
INPUT_LIMIT_ERROR = "diagram input exceeds the 16 MiB limit"
RAW_MARKUP_RE = re.compile(r"</?[a-zA-Z]|<\?|<!(?!\[CDATA\[|--)")
RAW_TEXT_TAGS = {"style", "script", "title", "textarea", "xmp", "iframe", "noembed", "noframes", "plaintext"}


def read_local_utf8(path: Path) -> str:
    """Read at most the input limit plus one byte, then decode strictly."""
    with path.open("rb") as stream:
        content = stream.read(MAX_INPUT_BYTES + 1)
    if len(content) > MAX_INPUT_BYTES:
        raise ValueError(INPUT_LIMIT_ERROR)
    # Match read_text's universal-newline behavior used by the existing helpers.
    return content.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")

CSS_ESCAPE_RE = re.compile(r"\\(?:([0-9a-fA-F]{1,6})[ \t\r\n\f]?|(.))", re.DOTALL)
CSS_TOKEN_RE = re.compile(
    r'''/\*[\s\S]*?(?:\*/|$)|"(?:\\[\s\S]|[^"\\\r\n\f])*"|'(?:\\[\s\S]|[^'\\\r\n\f])*'|(?:[\w-]|\\(?:[0-9a-fA-F]{1,6}[ \t\r\n\f]?|[\s\S]))+|[^\s]'''
)
RESOURCE_ATTRS = {
    "href", "src", "srcset", "imagesrcset", "poster", "action", "formaction",
    "background", "data", "codebase", "archive", "manifest", "ping", "profile",
    "longdesc", "lowsrc", "dynsrc", "classid", "icon", "xml:base",
}
CSS_ATTRS = {
    "style", "fill", "stroke", "filter", "clip-path", "mask", "marker",
    "marker-start", "marker-mid", "marker-end", "cursor",
}
FORBIDDEN_TAGS = {
    "script", "base", "embed", "object", "iframe", "frame", "frameset",
    "foreignobject", "animate", "animatecolor", "animatemotion", "animatetransform", "animation", "set",
    "discard", "handler", "listener", "audio", "video", "applet", "marquee",
}
NAMESPACES = {
    "http://www.w3.org/2000/svg", "http://www.w3.org/1999/xhtml",
    "http://www.w3.org/1999/xlink", "http://www.w3.org/XML/1998/namespace",
}


def normalize_css_escapes(source: str) -> str:
    source = source.replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n")

    def replace(match: re.Match[str]) -> str:
        if match.group(1) is None:
            return "" if match.group(2) == "\n" else match.group(2)
        codepoint = int(match.group(1), 16)
        return chr(codepoint) if 0 < codepoint <= 0x10FFFF and not 0xD800 <= codepoint <= 0xDFFF else "\ufffd"

    return CSS_ESCAPE_RE.sub(replace, source)


def css_errors(source: str) -> list[str]:
    # Tokenize BEFORE decoding escapes: an escaped quote is not a string boundary,
    # and comment delimiters inside a string are literal text.
    tokens = []
    for match in CSS_TOKEN_RE.finditer(source.replace("\r\n", "\n")):
        token = match.group()
        if token.startswith("/*"):
            continue
        quoted = token.startswith(("'", '"')) and len(token) > 1
        tokens.append((normalize_css_escapes(token[1:-1] if quoted else token), quoted))
    errors = []
    for index, (token, quoted) in enumerate(tokens):
        if quoted:
            continue
        lowered = token.casefold()
        previous = tokens[index - 1][0] if index else ""
        following = tokens[index + 1][0] if index + 1 < len(tokens) else ""
        if previous == "@" and lowered == "import":
            errors.append("CSS @import is not allowed")
        if previous == "@" and re.fullmatch(r"(?:-[a-z]+-)?keyframes", lowered):
            errors.append("CSS animation is not allowed")
        if following == ":" and re.fullmatch(r"(?:-[a-z]+-)?(?:animation|transition)(?:-[\w-]+)?", lowered):
            errors.append("CSS animation/transition is not allowed")
        if lowered in {"behavior", "-moz-binding"} and following == ":":
            errors.append("executable CSS is not allowed")
        if following != "(":
            continue
        if lowered in {"image-set", "-webkit-image-set", "image", "src", "expression", "paint"}:
            errors.append(f"CSS {lowered}() is not allowed")
        if lowered == "url":
            end = index + 2
            while end < len(tokens) and tokens[end] != (")", False):
                end += 1
            value = "".join(part for part, _ in tokens[index + 2:end]).strip()
            if end == len(tokens) or not value.startswith("#") or any(
                part == "(" and not literal for part, literal in tokens[index + 2:end]
            ):
                errors.append("non-fragment CSS url() is not allowed")
    return errors


def element_errors(tag: str, attrs: list[tuple[str, str | None]]) -> list[str]:
    tag = tag.rsplit("}", 1)[-1].rsplit(":", 1)[-1].casefold()
    errors = []
    if tag in FORBIDDEN_TAGS:
        errors.append(f"<{tag}> is not allowed in a static diagram")
    data = {key.casefold(): value or "" for key, value in attrs}
    if tag == "meta" and any(key == "http-equiv" for key in data):
        errors.append("meta http-equiv is not allowed")
    for key, value in attrs:
        key = key.casefold()
        value = value or ""
        local = key.rsplit("}", 1)[-1].rsplit(":", 1)[-1]
        if key == "xmlns" or key.startswith("xmlns:"):
            if value not in NAMESPACES:
                errors.append("unsupported namespace declaration")
            continue  # Namespace URIs are identifiers, not resource requests.
        if local.startswith("on") or local == "srcdoc":
            errors.append(f"executable attribute {key} on <{tag}>")
        if local in RESOURCE_ATTRS or key == "xml:base" or key.endswith("}base"):
            if local in {"srcset", "imagesrcset", "ping", "archive"} or not value.strip().startswith("#"):
                errors.append(f"non-fragment resource reference on <{tag}>: {value[:80]}")
        if local in CSS_ATTRS:
            errors.extend(css_errors(value))
    return errors


class SafetyParser(HTMLParser):
    def __init__(self) -> None:
        # Keep entity-escaped tag prose distinct from literal markup in text.
        # HTMLParser still decodes attribute values with this setting.
        super().__init__(convert_charrefs=False)
        self.errors: list[str] = []
        self.styles: list[str] = []
        self.style_depth = 0
        self.raw_text_tag: str | None = None

    def handle_starttag(self, tag, attrs):
        if self.raw_text_tag:
            self.errors.append(f"markup inside {self.raw_text_tag} text is not allowed")
        self.errors.extend(element_errors(tag, attrs))
        local = tag.casefold().rsplit(":", 1)[-1]
        if local in RAW_TEXT_TAGS:
            self.raw_text_tag = local
        if local == "style":
            self.style_depth += 1

    def handle_endtag(self, tag):
        local = tag.casefold().rsplit(":", 1)[-1]
        if local == self.raw_text_tag:
            self.raw_text_tag = None
        if local == "style":
            self.style_depth = max(0, self.style_depth - 1)

    def handle_data(self, data):
        # Foreign-content parsing can turn literal tags into HTML even inside
        # CSS strings/comments or SVG elements whose HTML names imply raw text.
        # Refuse markup rather than emulate browser namespace/tree-building rules.
        if self.raw_text_tag and RAW_MARKUP_RE.search(data):
            self.errors.append(f"markup inside {self.raw_text_tag} text is not allowed")
        if self.style_depth:
            self.styles.append(data)

    def handle_pi(self, data):
        if not re.fullmatch(r'xml\s+version=["\']1\.0["\'](?:\s+encoding=["\']UTF-8["\'])?\s*\?', data, re.I):
            self.errors.append("processing instructions are not allowed")

    def handle_decl(self, decl):
        if decl.casefold().strip() != "doctype html":
            self.errors.append("external or custom declarations are not allowed")

    def unknown_decl(self, data):
        if not data.startswith("CDATA["):
            self.errors.append("unsupported markup declaration")
        elif RAW_MARKUP_RE.search(data):
            # Outside SVG, browsers treat a CDATA opener as a bogus comment
            # ending at the first >, potentially exposing its remaining tags.
            self.errors.append("markup inside CDATA is not allowed")


def safety_errors(source: str, *, xml: bool = False) -> list[str]:
    """Check safety only, independently of diagram naming/layout requirements."""
    if len(source) > MAX_INPUT_BYTES:
        return [INPUT_LIMIT_ERROR]
    # Bound the temporary encoding allocation as well as the accepted byte size.
    byte_count = 0
    for start in range(0, len(source), 65536):
        try:
            byte_count += len(source[start:start + 65536].encode("utf-8"))
        except UnicodeEncodeError:
            return ["diagram input is not valid UTF-8 text"]
        if byte_count > MAX_INPUT_BYTES:
            return [INPUT_LIMIT_ERROR]
    # HTMLParser and a browser can disagree about where these comments end.
    # Refuse them rather than allowing active markup to hide in a parser comment.
    if re.search(r"<!--(?:>|->)|--!>", source):
        return ["ambiguous HTML comment termination is not allowed"]
    parser = SafetyParser()
    try:
        parser.feed(source)
        parser.close()
    except (ValueError, AssertionError) as exc:
        return [f"cannot safely parse diagram markup: {exc}"]
    errors = parser.errors
    if parser.style_depth:
        errors.append("unclosed style element is not allowed")
    if parser.raw_text_tag:
        errors.append(f"unclosed {parser.raw_text_tag} text element is not allowed")
    errors.extend(css_errors("\n".join(parser.styles)))
    # HTML style text is raw, but SVG style text can contain XML references.
    # Inspect the decoded spelling too so encoded loader names cannot evade
    # the HTML self-check. Export additionally checks the actual XML tree.
    errors.extend(css_errors(unescape("\n".join(parser.styles))))
    if xml:
        try:
            root = ET.fromstring(source)
        except ET.ParseError as exc:
            errors.append(f"SVG is not well-formed XML: {exc}")
        else:
            for node in root.iter():
                errors.extend(element_errors(node.tag, list(node.attrib.items())))
                if node.tag.rsplit("}", 1)[-1].casefold() == "style":
                    errors.extend(css_errors("".join(node.itertext())))
    return list(dict.fromkeys(errors))


def assert_static_safe(source: str, *, xml: bool = False) -> None:
    errors = safety_errors(source, xml=xml)
    if errors:
        raise ValueError("unsafe static diagram: " + "; ".join(errors))
