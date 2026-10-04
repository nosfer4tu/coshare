import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# api/_lib modules import each other as top-level modules; verified_checks.py is pure
# (no config/db import), so no env vars or DB access are needed.
sys.path.insert(0, str(ROOT / "api" / "_lib"))
sys.path.insert(0, str(ROOT))

from verified_checks import validate_check, MATCH_TOLERANCE  # noqa: E402
import seed_verified_checks  # noqa: E402


def make_record(**overrides):
    record = {
        "route": "AAA-BBB",
        "check_date": "2026-01-02",
        "flight_date": "2026-03-04",
        "carrier_checked": "Example Airlines",
        "sandbox_source": "duffel",
        "sandbox_price_jpy": 10000,
        "real_price_jpy": 10000,
        "real_source_url": "https://example.com/",
        "verdict": "match",
        "notes": None,
    }
    record.update(overrides)
    return record


class ValidateCheckTest(unittest.TestCase):
    def assertInvalid(self, record, fragment):
        errors = validate_check(record)
        self.assertTrue(any(fragment in e for e in errors), f"expected '{fragment}' in {errors}")

    def test_valid_match(self):
        self.assertEqual(validate_check(make_record()), [])

    def test_tolerance_constant_is_five_percent(self):
        self.assertEqual(MATCH_TOLERANCE, 0.05)

    def test_match_exactly_at_boundary_is_valid(self):
        self.assertEqual(validate_check(make_record(sandbox_price_jpy=10500, real_price_jpy=10000)), [])
        self.assertEqual(validate_check(make_record(sandbox_price_jpy=9500, real_price_jpy=10000)), [])

    def test_match_over_tolerance_rejected(self):
        self.assertInvalid(make_record(sandbox_price_jpy=10501, real_price_jpy=10000), "'match' requires")

    def test_mismatch_over_tolerance_valid(self):
        self.assertEqual(validate_check(make_record(verdict="mismatch", sandbox_price_jpy=12000)), [])

    def test_mismatch_within_tolerance_rejected(self):
        self.assertInvalid(make_record(verdict="mismatch", sandbox_price_jpy=10500), "'mismatch' requires")

    def test_not_comparable_with_null_or_zero_prices_valid(self):
        self.assertEqual(validate_check(make_record(
            verdict="not_comparable", sandbox_price_jpy=None, real_price_jpy=None,
            notes="公式サイトで該当便が見つからなかった")), [])
        self.assertEqual(validate_check(make_record(
            verdict="not_comparable", sandbox_price_jpy=0, real_price_jpy=0)), [])

    def test_not_comparable_with_verdict_implying_note_rejected(self):
        for note in ("価格は一致していた", "Prices match", "Mismatch on fare", "ほぼ同額", "verified OK"):
            with self.subTest(note=note):
                self.assertInvalid(make_record(
                    verdict="not_comparable", sandbox_price_jpy=None, real_price_jpy=None, notes=note),
                    "must not imply a verdict")

    def test_not_comparable_negative_price_rejected(self):
        self.assertInvalid(make_record(verdict="not_comparable", real_price_jpy=-1), "real_price_jpy")

    def test_match_requires_positive_integer_prices(self):
        for bad in (None, 0, -5, 100.5, "100", True):
            with self.subTest(bad=bad):
                self.assertInvalid(make_record(real_price_jpy=bad), "real_price_jpy")
                self.assertInvalid(make_record(sandbox_price_jpy=bad), "sandbox_price_jpy")

    def test_route_format(self):
        for bad in ("KIX-TPEE", "kix-tpe", "KIXTPE", "KIX-T1E", "", None, 123):
            with self.subTest(bad=bad):
                self.assertTrue(validate_check(make_record(route=bad)))

    def test_dates_must_be_iso(self):
        for field in ("check_date", "flight_date"):
            for bad in ("2026/01/02", "2026-13-01", "2026-02-30", "20260102", "", None, 20260102):
                with self.subTest(field=field, bad=bad):
                    self.assertTrue(validate_check(make_record(**{field: bad})))

    def test_real_source_url_must_be_https(self):
        for bad in ("http://example.com", "example.com", "ftp://example.com", "", None):
            with self.subTest(bad=bad):
                self.assertTrue(validate_check(make_record(real_source_url=bad)))

    def test_enums_enforced(self):
        self.assertInvalid(make_record(verdict="ok"), "verdict must be one of")
        self.assertInvalid(make_record(sandbox_source="amadeus"), "sandbox_source must be one of")
        self.assertEqual(validate_check(make_record(sandbox_source="flightlabs")), [])

    def test_carrier_required_non_blank(self):
        self.assertTrue(validate_check(make_record(carrier_checked="   ")))
        self.assertTrue(validate_check(make_record(carrier_checked=None)))

    def test_non_dict_rejected(self):
        self.assertEqual(validate_check(None), ["record must be an object"])


class SeedFileTest(unittest.TestCase):
    def test_example_entries_are_skipped(self):
        # Uses a temporary data file, so it does not depend on what the real
        # verified_checks_data.json currently holds.
        example = make_record(example=True, notes="PLACEHOLDER ONLY")
        real = make_record(route="CCC-DDD")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.json"
            path.write_text(json.dumps({"checks": [example, real]}), encoding="utf-8")
            records = seed_verified_checks.load_records(path)
        self.assertEqual(records, [real])

    def test_example_entry_is_itself_well_formed(self):
        import json
        with open(seed_verified_checks.DATA_FILE, encoding="utf-8") as f:
            checks = json.load(f)["checks"]
        examples = [c for c in checks if c.get("example") is True]
        self.assertEqual(len(examples), 1)
        self.assertEqual(validate_check(examples[0]), [])


if __name__ == "__main__":
    unittest.main()
