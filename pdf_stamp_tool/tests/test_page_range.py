import unittest

from core.exceptions import PageRangeFormatError
from core.page_range import parse_page_range


class PageRangeTests(unittest.TestCase):
    def test_parse_all_pages(self):
        self.assertEqual(parse_page_range("全部", 3), [0, 1, 2])

    def test_parse_mixed_range(self):
        self.assertEqual(parse_page_range("1,3-5,8", 10), [0, 2, 3, 4, 7])

    def test_parse_invalid_range(self):
        with self.assertRaises(PageRangeFormatError):
            parse_page_range("3-1", 5)


if __name__ == "__main__":
    unittest.main()
