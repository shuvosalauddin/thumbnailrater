import csv
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from scripts.calibrate import calibrate_weights
from scripts.prep_image import analyze_thumbnail
from scripts.score import score_thumbnail


class PrepImageTests(unittest.TestCase):
    def test_reports_measured_properties_for_standard_thumbnail(self):
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "thumb.png"
            image = Image.new("RGB", (1280, 720), "black")
            image.paste("white", (400, 200, 880, 520))
            image.save(image_path)

            result = analyze_thumbnail(image_path)

        self.assertEqual(result["original_resolution"], [1280, 720])
        self.assertTrue(result["is_standard_16_9"])
        self.assertEqual(result["mobile_preview"]["resolution"], [120, 68])
        self.assertGreater(result["visual_contrast"], 0)
        self.assertIn("not subject isolation", result["limitations"][0])

    def test_preserves_aspect_ratio_for_arbitrary_screenshot_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "screenshot.png"
            image = Image.new("RGB", (600, 400), "white")
            image.paste("black", (0, 0, 300, 400))
            image.save(image_path)

            result = analyze_thumbnail(image_path)

        preview_width, preview_height = result["mobile_preview"]["resolution"]
        self.assertLessEqual(preview_width, 120)
        self.assertLessEqual(preview_height, 68)
        self.assertAlmostEqual(preview_width / preview_height, 1.5, places=1)
        self.assertFalse(result["is_standard_16_9"])
        self.assertEqual(result["recommendations"], [])


class ScoreTests(unittest.TestCase):
    def test_uses_normalized_weights_for_score(self):
        result = score_thumbnail(
            {
                "subject_clarity": 100,
                "visual_contrast": 50,
                "title_synergy": 50,
                "cognitive_simplicity": 50,
            },
            {
                "subject_clarity": 3,
                "visual_contrast": 1,
                "title_synergy": 0,
                "cognitive_simplicity": 0,
            },
        )

        self.assertEqual(result["final_score"], 87.5)
        self.assertAlmostEqual(result["breakdown"]["subject_clarity"]["weight"], 0.75)
        self.assertIn("not a predicted CTR percentage", result["interpretation"])

    def test_does_not_penalize_non_16_9_screenshot(self):
        result = score_thumbnail(
            {
                "subject_clarity": 80,
                "visual_contrast": 80,
                "title_synergy": 80,
                "cognitive_simplicity": 80,
                "is_standard_16_9": False,
            }
        )

        self.assertEqual(result["final_score"], 80)
        self.assertEqual(result["actionable_feedback"], [
            "No low-scoring dimension was identified; review the image at feed size."
        ])

    def test_rejects_missing_or_out_of_range_ratings(self):
        with self.assertRaisesRegex(ValueError, "Missing required rating"):
            score_thumbnail({})
        with self.assertRaisesRegex(ValueError, "from 0 to 100"):
            score_thumbnail(
                {
                    "subject_clarity": 101,
                    "visual_contrast": 50,
                    "title_synergy": 50,
                    "cognitive_simplicity": 50,
                }
            )


class CalibrationTests(unittest.TestCase):
    def test_fits_and_emits_weights_compatible_with_scorer(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "ratings.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=[
                        "impressions",
                        "ctr_percentage",
                        "subject_clarity",
                        "visual_contrast",
                        "title_synergy",
                        "cognitive_simplicity",
                    ],
                )
                writer.writeheader()
                for index in range(10):
                    subject = index * 10
                    writer.writerow(
                        {
                            "impressions": 1000,
                            "ctr_percentage": 2 + subject * 0.05,
                            "subject_clarity": subject,
                            "visual_contrast": 50,
                            "title_synergy": 50,
                            "cognitive_simplicity": 50,
                        }
                    )

            model = calibrate_weights(csv_path)

        self.assertAlmostEqual(sum(model["weights"].values()), 1, places=5)
        self.assertGreater(model["weights"]["subject_clarity"], 0.99)
        self.assertEqual(model["training"]["videos"], 10)
        score = score_thumbnail(
            {
                "subject_clarity": 90,
                "visual_contrast": 50,
                "title_synergy": 50,
                "cognitive_simplicity": 50,
            },
            model["weights"],
        )
        self.assertGreater(score["final_score"], 50)

    def test_rejects_missing_csv_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "ratings.csv"
            csv_path.write_text("ctr_percentage\n5\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing required columns"):
                calibrate_weights(csv_path)


if __name__ == "__main__":
    unittest.main()
