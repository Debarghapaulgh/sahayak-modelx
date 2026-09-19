import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from synthetictutor.knowledge.locale_retriever import LocaleRetriever


class TestLocaleRetriever(unittest.TestCase):
    def setUp(self):
        locale_path = os.path.join(BASE_DIR, "locale.json")
        self.retriever = LocaleRetriever(locale_path=locale_path)

    def test_locale_structure(self):
        """Verify locale.json contains region_summary and districts."""
        data = self.retriever.locale_data
        self.assertIn("region_summary", data)
        self.assertIn("districts", data)
        self.assertEqual(data["region_summary"]["default_board"], "WBBSE")
        self.assertEqual(data["region_summary"]["default_medium"], "Bengali")

    def test_district_count(self):
        """Verify North Bengal districts are properly mapped."""
        districts = self.retriever.locale_data["districts"]
        self.assertGreaterEqual(len(districts), 8)

    def test_localization_triggers(self):
        """Verify trigger detection for localization phrases."""
        self.assertTrue(self.retriever.is_localization_requested("জলপাইগুড়ি জেলার চা বাগান সম্পর্কিত অংক"))
        self.assertFalse(self.retriever.is_localization_requested("সাধারণ বীজগণিত সমাধান করো"))


if __name__ == "__main__":
    unittest.main()
