import unittest

from core.units import mm_to_pt, pt_to_mm


class UnitTests(unittest.TestCase):
    def test_mm_pt_roundtrip(self):
        value = 42.5
        self.assertLess(abs(pt_to_mm(mm_to_pt(value)) - value), 0.0001)


if __name__ == "__main__":
    unittest.main()
