"""Measure basic image and small-preview properties of a thumbnail."""

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image


def _percentile_range(image: Image.Image) -> int:
    histogram = image.histogram()
    pixel_count = sum(histogram)
    low_target = pixel_count * 0.05
    high_target = pixel_count * 0.95
    cumulative = 0
    low = 0
    high = 255

    for value, count in enumerate(histogram):
        cumulative += count
        if cumulative >= low_target:
            low = value
            break

    cumulative = 0
    for value, count in enumerate(histogram):
        cumulative += count
        if cumulative >= high_target:
            high = value
            break

    return high - low


def _image_metrics(image: Image.Image) -> dict[str, int | float]:
    grayscale = image.convert("L")
    low, high = grayscale.getextrema()
    return {
        "min_max_range": high - low,
        "p5_p95_range": _percentile_range(grayscale),
        "rms_contrast": round(_rms_contrast(grayscale), 2),
    }


def _small_preview(image: Image.Image) -> Image.Image:
    preview = image.copy()
    preview.thumbnail((120, 68), Image.Resampling.LANCZOS)
    return preview


def _rms_contrast(image: Image.Image) -> float:
    histogram = image.histogram()
    pixel_count = sum(histogram)
    mean = sum(value * count for value, count in enumerate(histogram)) / pixel_count
    variance = sum(count * (value - mean) ** 2 for value, count in enumerate(histogram)) / pixel_count
    return variance**0.5


def analyze_thumbnail(image_path: str | Path) -> dict[str, Any]:
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")

    with Image.open(path) as source:
        image = source.convert("RGB")

    width, height = image.size
    if width == 0 or height == 0:
        raise ValueError("Image must have non-zero width and height.")
    aspect_ratio = width / height
    is_16_9 = abs(aspect_ratio - (16 / 9)) < 0.02
    mobile_preview = _small_preview(image)
    original_metrics = _image_metrics(image)
    mobile_metrics = _image_metrics(mobile_preview)
    contrast_score = min(100, round(mobile_metrics["p5_p95_range"] / 1.8))

    recommendations = []
    if mobile_metrics["p5_p95_range"] < 90:
        recommendations.append("The small preview has a narrow tonal range; inspect subject/background separation.")

    return {
        "original_resolution": [width, height],
        "aspect_ratio": round(aspect_ratio, 3),
        "is_standard_16_9": is_16_9,
        "measured_contrast": original_metrics,
        "mobile_preview": {
            "resolution": list(mobile_preview.size),
            "measured_contrast": mobile_metrics,
        },
        "visual_contrast": contrast_score,
        "recommendations": recommendations,
        "limitations": [
            "Contrast metrics describe grayscale tonal spread, not subject isolation or visual saliency.",
            "Text density and legibility require visual inspection or a separate OCR-based tool.",
            "Aspect ratio and resolution describe the supplied image; they are not design-quality scores.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", help="Path to a thumbnail image")
    args = parser.parse_args()
    try:
        result = analyze_thumbnail(args.image)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
