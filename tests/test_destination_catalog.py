import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# destination_catalog.py is pure (stdlib only), so no env vars or DB access are needed.
sys.path.insert(0, str(ROOT / "api" / "_lib"))

from destination_catalog import (  # noqa: E402
    ALLOWED_TAGS, CatalogError, DATA_FILE, load_catalog, validate_catalog, validate_entry,
)


def make_items(count, title_field):
    return [
        {title_field: f"item{i}", "note": "note", "sourceUrl": "https://example.com/"}
        for i in range(count)
    ]


def make_entry(**overrides):
    entry = {
        "iata": "AAA",
        "city": "サンプル市",
        "country": "サンプル国",
        "bestMonths": [1, 12],
        "budgetLevel": 2,
        "tags": ["food", "city"],
        "highlights": make_items(3, "title"),
        "hotelAreas": make_items(2, "name"),
        "mapQuery": "サンプル市",
        "lastChecked": "2026-01-02",
    }
    entry.update(overrides)
    return entry


class ValidateEntryTest(unittest.TestCase):
    def assertInvalid(self, entry, fragment):
        errors = validate_entry(entry)
        self.assertTrue(any(fragment in e for e in errors), f"expected '{fragment}' in {errors}")

    def test_valid_entry(self):
        self.assertEqual(validate_entry(make_entry()), [])

    def test_caution_is_optional(self):
        self.assertEqual(validate_entry(make_entry(caution="注意")), [])
        self.assertInvalid(make_entry(caution=""), "caution")

    def test_unknown_tag_rejected(self):
        self.assertInvalid(make_entry(tags=["food", "skiing"]), "unknown tag")

    def test_all_allowed_tags_accepted(self):
        self.assertEqual(
            ALLOWED_TAGS, {"food", "city", "culture", "nature", "beach", "shopping", "nightlife", "relax"})
        self.assertEqual(validate_entry(make_entry(tags=sorted(ALLOWED_TAGS))), [])

    def test_month_outside_range_rejected(self):
        for bad in ([0], [13], [1, 13], [-1], ["1"], [True], [1.5]):
            with self.subTest(bad=bad):
                self.assertInvalid(make_entry(bestMonths=bad), "bestMonths")

    def test_budget_level_range(self):
        for good in (1, 2, 3):
            self.assertEqual(validate_entry(make_entry(budgetLevel=good)), [])
        for bad in (0, 4, "2", True, 2.0):
            with self.subTest(bad=bad):
                self.assertInvalid(make_entry(budgetLevel=bad), "budgetLevel")

    def test_highlight_source_url_must_be_https(self):
        for bad in ("http://example.com", "example.com", "ftp://example.com", "https://", "", None):
            with self.subTest(bad=bad):
                highlights = make_items(3, "title")
                highlights[1]["sourceUrl"] = bad
                self.assertInvalid(make_entry(highlights=highlights), "highlights[1].sourceUrl")

    def test_hotel_area_source_url_must_be_https(self):
        for bad in ("http://example.com", "example.com", "https://", "", None):
            with self.subTest(bad=bad):
                areas = make_items(2, "name")
                areas[0]["sourceUrl"] = bad
                self.assertInvalid(make_entry(hotelAreas=areas), "hotelAreas[0].sourceUrl")

    def test_highlight_count_must_be_three_to_five(self):
        for good in (3, 4, 5):
            self.assertEqual(validate_entry(make_entry(highlights=make_items(good, "title"))), [])
        for bad in (0, 2, 6):
            with self.subTest(bad=bad):
                self.assertInvalid(make_entry(highlights=make_items(bad, "title")), "highlights must have 3 to 5")

    def test_hotel_area_count_must_be_two_to_three(self):
        for good in (2, 3):
            self.assertEqual(validate_entry(make_entry(hotelAreas=make_items(good, "name"))), [])
        for bad in (0, 1, 4):
            with self.subTest(bad=bad):
                self.assertInvalid(make_entry(hotelAreas=make_items(bad, "name")), "hotelAreas must have 2 to 3")

    def test_item_fields_required(self):
        areas = make_items(2, "name")
        areas[0]["note"] = ""
        self.assertInvalid(make_entry(hotelAreas=areas), "hotelAreas[0].note")
        highlights = make_items(3, "title")
        del highlights[2]["title"]
        self.assertInvalid(make_entry(highlights=highlights), "highlights[2].title")

    def test_empty_map_query_rejected(self):
        for bad in ("", "   ", None, 123):
            with self.subTest(bad=bad):
                self.assertInvalid(make_entry(mapQuery=bad), "mapQuery")

    def test_missing_last_checked_rejected(self):
        entry = make_entry()
        del entry["lastChecked"]
        self.assertInvalid(entry, "lastChecked is required")
        self.assertInvalid(make_entry(lastChecked=None), "lastChecked is required")

    def test_last_checked_must_be_iso_date(self):
        for bad in ("2026/01/02", "2026-13-01", "2026-02-30", "20260102", 20260102):
            with self.subTest(bad=bad):
                self.assertInvalid(make_entry(lastChecked=bad), "lastChecked")

    def test_iata_format(self):
        for bad in ("aaa", "AA", "AAAA", "A1A", "", None, 123):
            with self.subTest(bad=bad):
                self.assertTrue(validate_entry(make_entry(iata=bad)))

    def test_required_fields(self):
        for field in ("iata", "city", "country", "bestMonths", "budgetLevel", "tags",
                      "highlights", "hotelAreas", "mapQuery", "lastChecked"):
            with self.subTest(field=field):
                entry = make_entry()
                del entry[field]
                self.assertInvalid(entry, f"{field} is required")

    def test_non_dict_rejected(self):
        self.assertEqual(validate_entry(None), ["entry must be an object"])


class ValidateCatalogTest(unittest.TestCase):
    def test_valid_catalog(self):
        self.assertEqual(validate_catalog([make_entry(), make_entry(iata="BBB")]), [])

    def test_duplicate_iata_rejected(self):
        errors = validate_catalog([make_entry(), make_entry(iata="BBB"), make_entry()])
        self.assertTrue(any("duplicate iata" in e and "destinations[2]" in e for e in errors), errors)

    def test_entry_errors_name_the_entry(self):
        errors = validate_catalog([make_entry(), make_entry(iata="BBB", budgetLevel=9)])
        self.assertTrue(any(e.startswith("destinations[1] (BBB):") for e in errors), errors)


class LoadCatalogTest(unittest.TestCase):
    def write_catalog(self, tmp, destinations):
        path = Path(tmp) / "catalog.json"
        path.write_text(json.dumps({"destinations": destinations}), encoding="utf-8")
        return path

    def test_example_entries_are_skipped(self):
        # Uses a temporary file, so it does not depend on what the real catalog holds.
        example = make_entry(iata="ZZZ", example=True, mapQuery="")  # invalid, but skipped
        real = make_entry(iata="BBB")
        with tempfile.TemporaryDirectory() as tmp:
            entries = load_catalog(self.write_catalog(tmp, [example, real]))
        self.assertEqual(entries, [real])

    def test_example_does_not_count_as_duplicate(self):
        example = make_entry(example=True)
        real = make_entry()
        with tempfile.TemporaryDirectory() as tmp:
            entries = load_catalog(self.write_catalog(tmp, [example, real]))
        self.assertEqual(entries, [real])

    def test_invalid_entry_raises_with_all_errors(self):
        bad = make_entry(budgetLevel=9, mapQuery="")
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_catalog(tmp, [bad])
            with self.assertRaises(CatalogError) as ctx:
                load_catalog(path)
        self.assertIn("budgetLevel", str(ctx.exception))
        self.assertIn("mapQuery", str(ctx.exception))


class CatalogFileTest(unittest.TestCase):
    def test_example_entry_is_itself_well_formed(self):
        with open(DATA_FILE, encoding="utf-8") as f:
            destinations = json.load(f)["destinations"]
        examples = [d for d in destinations if d.get("example") is True]
        self.assertEqual(len(examples), 1)
        self.assertEqual(validate_entry(examples[0]), [])

    def test_real_catalog_loads(self):
        # Passes with zero real entries today; fails as soon as an added entry is invalid.
        load_catalog()


if __name__ == "__main__":
    unittest.main()
