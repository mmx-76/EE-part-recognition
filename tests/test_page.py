"""Checks on the web page itself.  Run with:  py -m unittest discover tests

These catch a whole class of mistake that the other tests can't see: the page's JavaScript
looking for an element (a button, a box) that isn't actually in the HTML."""
import os
import re
import unittest

PAGE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates", "index.html")


class PageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(PAGE, encoding="utf-8") as handle:
            cls.html = handle.read()
        cls.script = cls.html[cls.html.index("<script>"):]
        cls.markup = cls.html[:cls.html.index("<script>")]

    def test_every_element_the_script_looks_up_exists(self):
        defined = set(re.findall(r'id="([^"]+)"', self.markup))
        looked_up = set(re.findall(r'getElementById\("([^"]+)"\)', self.script))
        for line in re.findall(r'for \(const id of \[([^\]]+)\]', self.script):  # lists of ids
            looked_up |= set(re.findall(r'"([^"]+)"', line))
        self.assertEqual(sorted(looked_up - defined), [], "script uses ids missing from the page")

    def test_no_duplicate_ids(self):
        ids = re.findall(r'id="([^"]+)"', self.markup)
        self.assertEqual(sorted({i for i in ids if ids.count(i) > 1}), [])

    def test_advanced_options_and_size_field_are_present(self):
        for needed in ("optPins", "optGender", "optSize", "optIndustry", "optLimit", "optChecked",
                       "detailSize", "searchButton", "updateButton", "onlyUnchecked"):
            self.assertIn('id="%s"' % needed, self.markup)


if __name__ == "__main__":
    unittest.main()
