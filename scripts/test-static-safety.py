#!/usr/bin/env python3
"""Adversarial local/static boundary checks shared by self-check and SVG export."""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills/diagram-design/scripts"))
import export_svg
import self_check
import static_safety
from static_safety import safety_errors

DIAGRAM = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" '
           'role="img" aria-labelledby="safe-title safe-desc">'
           '<title id="safe-title">Safe</title><desc id="safe-desc">One box.</desc>'
           '<rect width="5" height="5"/></svg>')


def page(extra: str) -> str:
    return '<!doctype html><html><head><title>Diagram</title></head><body>' + extra + DIAGRAM + '</body></html>'


class StaticSafetyTests(unittest.TestCase):
    def test_foreign_style_and_cdata_cannot_hide_active_markup(self):
        template = (ROOT / 'skills/diagram-design/assets/template.html').read_text(encoding='utf-8')
        active = '<img src="https://example.test/a.png" onerror="alert(1)">'
        cases = [
            template.replace('</svg>', '<style>' + active + '</style></svg>', 1),
            template.replace('</svg>', '<style>.x {content:\'' + active + '\'}</style></svg>', 1),
            template.replace('</svg>', '<style>/*' + active + '*/</style></svg>', 1),
            template.replace('</svg>', '<style><svg><style>' + active + '</style></svg></style></svg>', 1),
            template.replace('</svg>', '<s:style xmlns:s="http://www.w3.org/2000/svg"><s:style/>.x {fill:url(remote.svg)}</s:style></svg>', 1),
            template.replace('</body>', '<![CDATA[><script>alert(1)</script>]]></body>', 1),
            template.replace('</body>', '<![CDATA[>' + active + ']]></body>', 1),
        ]
        cases.extend(template.replace('</svg>', '<' + tag + '>' + active + '</' + tag + '></svg>', 1)
                     for tag in ('title', 'textarea', 'xmp', 'noembed', 'noframes', 'plaintext'))
        cases.extend(template + '<svg><' + tag + '>' + active
                     for tag in ('style', 'title', 'textarea', 'xmp'))
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'foreign.html'
            output = Path(folder) / 'foreign.svg'
            for html in cases:
                with self.subTest(html=html[-400:]):
                    source.write_text(html, encoding='utf-8')
                    self.assertTrue(safety_errors(html))
                    self.assertTrue(self_check.verify(source))
                    with self.assertRaisesRegex(ValueError, 'unsafe static diagram'):
                        export_svg.export_svg_document(html, source)
                    with contextlib.redirect_stderr(io.StringIO()):
                        self.assertEqual(export_svg.main([str(source), str(output)]), 2)
                    self.assertFalse(output.exists())
        self.assertEqual(safety_errors('<title>Literal &lt;img&gt; prose</title>'), [])

    def test_oversized_files_fail_before_parsing_and_leave_outputs_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'large.html'
            output = Path(folder) / 'large.svg'
            source.write_bytes(b' ' * (static_safety.MAX_INPUT_BYTES + 1))
            with patch.object(self_check, 'parsed_document') as parser:
                with self.assertRaisesRegex(ValueError, '16 MiB limit'):
                    self_check.verify(source)
                parser.assert_not_called()
            for existing in (False, True):
                if existing:
                    output.write_text('existing output', encoding='utf-8')
                errors = io.StringIO()
                with patch.object(export_svg, 'export_svg_document') as transform:
                    with contextlib.redirect_stderr(errors):
                        self.assertEqual(export_svg.main([str(source), str(output)]), 2)
                    transform.assert_not_called()
                self.assertIn('16 MiB limit', errors.getvalue())
                if existing:
                    self.assertEqual(output.read_text(encoding='utf-8'), 'existing output')
                else:
                    self.assertFalse(output.exists())
            # The exact cap is allowed; rejection uses bytes actually read.
            with source.open('r+b') as stream:
                stream.truncate(static_safety.MAX_INPUT_BYTES)
            self.assertEqual(len(static_safety.read_local_utf8(source)), static_safety.MAX_INPUT_BYTES)

    def test_oversized_strings_fail_before_parsing_including_multibyte_text(self):
        for source in ('x' * (static_safety.MAX_INPUT_BYTES + 1),
                       'é' * (static_safety.MAX_INPUT_BYTES // 2 + 1)):
            with self.subTest(char=source[0]):
                with patch.object(static_safety, 'SafetyParser') as parser:
                    self.assertEqual(safety_errors(source), [static_safety.INPUT_LIMIT_ERROR])
                    with self.assertRaisesRegex(ValueError, '16 MiB limit'):
                        export_svg.export_svg_document(source, Path('large.html'))
                    parser.assert_not_called()

    def test_active_markup_and_resource_references_fail_both_entry_points(self):
        cases = [
            '<script>alert(1)</script>', '<script type="application/json">{}</script>',
            '<script data-diagram-controls></script>', '<svg onload="alert(1)"/>',
            '<g onclick="alert(1)"/>', '<iframe srcdoc="&lt;script>1&lt;/script>"/>',
            '<object data="file:///private.txt"/>', '<embed src="relative.svg"/>',
            '<base href="https://example.test/"/>', '<meta http-equiv="refresh" content="0;url=https://example.test/">',
            '<svg><foreignObject><div>Text</div></foreignObject></svg>',
            '<svg><animate attributeName="x" from="0" to="1"/></svg>',
            '<svg><animateMotion path="M0 0L1 1"/></svg>',
            '<svg><animateColor attributeName="fill" from="red" to="blue"/></svg>',
            '<svg><animation/></svg>',
            '<svg><animateTransform attributeName="transform"/></svg>',
            '<svg><set attributeName="href" to="https://example.test/"/></svg>',
            '<svg><discard/></svg>', '<svg><s:script xmlns:s="http://www.w3.org/2000/svg"/></svg>',
            '<svg><use xlink:href="file:///private.svg#shape"/></svg>',
            '<svg xml:base="https://example.test/"><use href="#shape"/></svg>',
            '<img src="https://example.test/a.png">', '<img src="//example.test/a.png">',
            '<img src="relative.png">', '<img src="../private.png">', '<img src="/private.png">',
            '<img src="file:///private.png">', '<img src="data:image/png;base64,AAAA">',
            '<img src="data:image/svg+xml,&lt;svg onload=alert(1)>">',
            '<img srcset="#safe 1x, https://example.test/a.png 2x">',
            '<a href="#safe" ping="#safe https://example.test/">Text</a>',
            '<body background="private.png">', '<form action="file:///private.txt"/>',
            '<a href="java&#x09;script:alert(1)">Text</a>', '<img src="">',
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist">',
            '<link href="https://fonts.googleapis.com.evil.test/css2">',
            '<?xml-stylesheet href="file:///private.css"?>',
            '<!DOCTYPE svg SYSTEM "file:///private.dtd">',
            '<!DOCTYPE svg [<!ENTITY secret SYSTEM "file:///private.txt">]>',
            '<svg xmlns="http://www.w3.org/1999/xhtml"><script/></svg>',
            '<!--><script>alert(1)</script><!-- -->',
            '<!---><script>alert(1)</script><!-- -->',
            '<!-- hidden --!><script>alert(1)</script><!-- -->',
        ]
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'input.html'
            output = Path(folder) / 'output.svg'
            for markup in cases:
                with self.subTest(markup=markup):
                    html = page(markup)
                    source.write_text(html, encoding='utf-8')
                    self.assertTrue(safety_errors(html))
                    self.assertTrue(self_check.verify(source))
                    self.assertTrue(self_check.verify(source, offline=True))
                    with patch.object(export_svg, 'extract_first_svg') as extraction:
                        with self.assertRaisesRegex(ValueError, 'unsafe static diagram'):
                            export_svg.export_svg_document(html, source)
                        extraction.assert_not_called()
                    with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(export_svg.main([str(source), str(output)]), 2)
                    self.assertFalse(output.exists())
                    output.write_text('existing output', encoding='utf-8')
                    with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(export_svg.main([str(source), str(output), '--system-fonts']), 2)
                    self.assertEqual(output.read_text(encoding='utf-8'), 'existing output')
                    output.unlink()

    def test_css_loaders_and_motion_fail_in_styles_and_attributes(self):
        cases = [
            '@import "remote.css";', r'@\69mport "remote.css";',
            'fill:url(https://example.test/a.svg#paint)', 'fill:url(//example.test/a.svg)',
            'fill:url(file:///private.svg)', 'fill:url(local.svg)', 'fill:url(data:image/png,AAAA)',
            r'fill:\75rl(https\3a //example.test/a.svg)', r'fill:u\72l("private.svg")',
            'fill:url("file:\\\n///private.svg")', 'background:image-set("private.png" 1x)',
            r'background:\69mage-set("private.png" 1x)', 'background:image("private.png")',
            'src:src("private.woff2")', 'width:expression(alert(1))',
            '-moz-binding:url(#binding)', 'behavior:url(#binding)',
            'animation:pulse 1s', r'\61nimation-name:pulse', 'transition:fill 1s',
            '-webkit-animation:pulse 1s', '@keyframes pulse {from {opacity:0}}',
            r'@\6b eyframes pulse {from {opacity:0}}',
            '@font-face {font-family:X;src:url("private.woff2")}',
            'content:"/*"; fill:url(private.svg); --text:"*/"',
            'content:"broken\n; fill:url(private.svg); /*"*/',
            "content:'broken\r; fill:url(private.svg); /*'*/",
            'content:"broken\f; fill:url(private.svg); /*"*/',
            'fill:url(var(--remote))', '@supports (fill:url(private.svg)) {.x {fill:red}}',
            '@layer outer {@media screen {.x {animation:pulse 1s}}}',
            '.x {fill:red; & .y {animation-name:pulse}}',
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'css.html'
            for css in cases:
                for markup in ('<style>' + css + '</style>', '<g style="' + css.replace('&', '&amp;').replace('"', '&quot;') + '"/>'):
                    with self.subTest(css=css, markup=markup):
                        source = page(markup)
                        path.write_text(source, encoding='utf-8')
                        self.assertTrue(self_check.verify(path))
                        with self.assertRaisesRegex(ValueError, 'unsafe static diagram'):
                            export_svg.export_svg_document(source, path)

    def test_svg_entity_and_cdata_styles_cannot_hide_loaders(self):
        for body in ('&#117;rl(file:///private.svg)', '<![CDATA[url(file:///private.svg)]]>'):
            source = '<svg viewBox="0 0 10 10"><style>.x {fill:' + body + '}</style><rect class="x"/></svg>'
            with self.subTest(body=body):
                self.assertTrue(safety_errors(source))
                with self.assertRaises(ValueError):
                    export_svg.export_svg_document(source, Path('encoded.html'))

    def test_serialized_svg_is_checked_after_transformation(self):
        # XML-decoded attributes must be checked too, independent of the HTML
        # parser, and a future transform must not accidentally introduce scripts.
        with patch.object(export_svg, 'normalize_rgba_presentation_attrs', return_value='<svg xmlns="http://www.w3.org/2000/svg"><script/></svg>'):
            with self.assertRaisesRegex(ValueError, 'script'):
                export_svg.export_svg_document(DIAGRAM, Path('safe.html'))
        self.assertTrue(safety_errors('<svg xmlns="http://www.w3.org/2000/svg"><image href="&#102;ile:///private"/></svg>', xml=True))

    def test_safe_fragments_namespaces_literals_and_system_fonts_survive(self):
        source = ('<style>.paint {fill:url("#paint")} .label {font-family:Georgia,serif;'
                  'content:"@import url(remote.png) animation:pulse 1s /* literal */"}</style>'
                  '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 10 10">'
                  '<defs><linearGradient id="paint"/><g id="shape"><rect width="5" height="5"/></g></defs>'
                  '<use xlink:href="#shape"/><rect class="paint" fill="url(#paint)"/>'
                  '<text data-note="url(remote.png)">Animation is prose.</text></svg>')
        self.assertEqual(safety_errors(source), [])
        exported = export_svg.export_svg_document(source, Path('safe.html'))
        self.assertEqual(exported, export_svg.export_svg_document(source, Path('safe.html'), system_fonts=True))
        self.assertIn('id="safe-paint"', exported)
        self.assertIn('xlink:href="#safe-shape"', exported)
        self.assertNotIn('fonts.googleapis.com', exported)
        self.assertEqual(safety_errors(exported, xml=True), [])
        # Safety validation does not impose the full a11y contract on old inputs.
        self.assertIn('<svg', export_svg.export_svg_document('<svg viewBox="0 0 1 1"><rect/></svg>', Path('legacy.html')))

    def test_nested_static_css_is_preserved(self):
        for group in ('@layer base', '@container (min-width: 1px)', '@future-group paint'):
            source = '<style>' + group + ' {.paint {fill:red}}</style><svg viewBox="0 0 10 10"><rect class="paint"/></svg>'
            result = export_svg.export_svg_document(source, Path('group.html'))
            self.assertIn(group, result)
            self.assertIn('#group-root .paint { fill:red }', result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
