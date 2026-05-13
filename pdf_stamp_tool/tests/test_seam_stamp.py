from io import BytesIO
import unittest

from PIL import Image

from core.seam_stamp import build_seam_marks, split_seam_stamp_png
from core.units import mm_to_pt
from models.seam_config import SeamStampConfig


class SeamStampTests(unittest.TestCase):
    def test_build_right_side_seam_marks(self):
        config = SeamStampConfig(page_range_text="1-3", total_width_mm=90, total_height_mm=30)
        page_sizes = {0: (600, 800), 1: (600, 800), 2: (600, 800)}
        marks = build_seam_marks(config, 3, page_sizes, "stamp")
        self.assertEqual(len(marks), 3)
        self.assertLess(abs(marks[0].width_pt - mm_to_pt(30)), 0.0001)
        self.assertGreater(marks[0].x_pt, 0)

    def test_split_seam_stamp_png(self):
        image = Image.new("RGBA", (120, 40), (255, 0, 0, 255))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        slices = split_seam_stamp_png(buffer.getvalue(), 3)
        self.assertEqual(sorted(slices.keys()), ["0", "1", "2"])
        self.assertTrue(all(len(data) > 0 for data in slices.values()))


if __name__ == "__main__":
    unittest.main()
