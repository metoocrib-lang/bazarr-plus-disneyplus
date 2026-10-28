"""Offline configuration validation and CLI previews."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from scripts.validate_series import main, validate

ENTRY = {"tvdb_id": 123456, "series_url": "https://www.disneyplus.com/series/example/abc123", "mapping": "17x1-13=1x1\n17x14-26=2x1"}


class MappingValidationTests(unittest.TestCase):
    def test_checks_every_series_and_rejects_duplicate_even_with_disjoint_rules(self):
        for entry in (dict(ENTRY, tvdb_id=True), dict(ENTRY, tvdb_id=0),
                      dict(ENTRY, mapping=None), dict(ENTRY, series_url="https://example.com/"),
                      dict(ENTRY, mapping="1x1-2=1x1\n1x2=2x1"),
                      dict(ENTRY, bridge_token="never print me")):
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                validate(json.dumps([ENTRY, entry]))
        with self.assertRaises(ValueError):
            validate(json.dumps([ENTRY, dict(ENTRY, mapping="18x1=3x1")]))

    def test_shape_limits_and_identity(self):
        for raw in ('[]', '{}', '[', ' ' * 16385, json.dumps([ENTRY] * 33)):
            with self.subTest(raw=raw[:20]), self.assertRaises(ValueError):
                validate(raw)
        self.assertEqual(validate(json.dumps([dict(ENTRY, mapping="")])), [dict(ENTRY, mapping="")])

    def test_preview_and_unmapped_exit_codes_with_bom(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'map.json'
            path.write_text(json.dumps([ENTRY]), encoding='utf-8-sig')
            for episode, expected, text in [('15', 0, 'Disney+ T2E2'), ('27', 2, 'Sin equivalencia')]:
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(main([str(path), '--episode', '123456', '17', episode]), expected)
                self.assertIn(text, output.getvalue())
            path.write_text('{"secret":"do-not-echo",}', encoding='utf-8')
            output = io.StringIO()
            with contextlib.redirect_stderr(output):
                self.assertEqual(main([str(path)]), 1)
            self.assertNotIn('do-not-echo', output.getvalue())
