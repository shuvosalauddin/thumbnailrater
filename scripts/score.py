"""Combine measured contrast with explicit, human-assessed thumbnail dimensions."""

import argparse
import json
import math
from pathlib import Path
from typing import Any


DIMENSIONS = (
    "subject_clarity",
    "visual_contrast",
    "title_synergy",
    "cognitive_simplicity",
)
DEFAULT_WEIGHTS = {dimension: 0.25 for dimension in DIMENSIONS}


def _validate_rating(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number from 0 to 100.")
    try:
        numeric_value = float(value)
    except OverflowError as error:
        raise ValueError(f"{name} must be a finite number from 0 to 100.") from error
    if not math.isfinite(numeric_value) or not 0 <= numeric_value <= 100:
        raise ValueError(f"{name} must be from 0 to 100.")
    return numeric_value


def score_thumbnail(
    ratings: dict[str, Any],
    weights: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(ratings, dict):
        raise ValueError("Ratings JSON must be an object.")
    values = {}
    for dimension in DIMENSIONS:
        if dimension not in ratings:
            raise ValueError(f"Missing required rating: {dimension}")
        values[dimension] = _validate_rating(dimension, ratings[dimension])

    selected_weights = DEFAULT_WEIGHTS if weights is None else weights
    if not isinstance(selected_weights, dict):
        raise ValueError("Weights must be an object.")
    validated_weights = {}
    for dimension in DIMENSIONS:
        weight = selected_weights.get(dimension)
        if isinstance(weight, bool) or not isinstance(weight, (int, float)):
            raise ValueError(f"Weight for {dimension} must be a finite, non-negative number.")
        try:
            numeric_weight = float(weight)
        except OverflowError as error:
            raise ValueError(f"Weight for {dimension} must be a finite, non-negative number.") from error
        if not math.isfinite(numeric_weight) or numeric_weight < 0:
            raise ValueError(f"Weight for {dimension} must be a finite, non-negative number.")
        validated_weights[dimension] = numeric_weight

    weight_sum = sum(validated_weights.values())
    if weight_sum <= 0:
        raise ValueError("At least one scoring weight must be greater than zero.")
    normalized_weights = {key: value / weight_sum for key, value in validated_weights.items()}
    final_score = sum(values[key] * normalized_weights[key] for key in DIMENSIONS)

    feedback = []
    for dimension, value in values.items():
        if value < 50:
            feedback.append(f"Improve {dimension.replace('_', ' ')}; this rating is below 50/100.")
        elif value < 70:
            feedback.append(f"Consider refining {dimension.replace('_', ' ')}; this rating is below 70/100.")

    if feedback == []:
        feedback.append("No low-scoring dimension was identified; review the image at feed size.")

    return {
        "final_score": round(final_score, 1),
        "breakdown": {
            dimension: {
                "rating": round(values[dimension], 1),
                "weight": round(normalized_weights[dimension], 4),
                "weighted_points": round(values[dimension] * normalized_weights[dimension], 2),
            }
            for dimension in DIMENSIONS
        },
        "actionable_feedback": feedback,
        "interpretation": "A rough CTR-potential design checklist score, not a predicted CTR percentage or guaranteed performance.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ratings_json", help="JSON file with image metrics and human ratings")
    parser.add_argument("--weights", help="Optional calibration JSON produced by calibrate.py")
    args = parser.parse_args()

    try:
        with Path(args.ratings_json).open(encoding="utf-8") as file:
            ratings = json.load(file)
        weights = None
        if args.weights:
            with Path(args.weights).open(encoding="utf-8") as file:
                calibration = json.load(file)
            if not isinstance(calibration, dict):
                raise ValueError("Calibration JSON must be an object.")
            weights = calibration.get("weights")
            if not isinstance(weights, dict):
                raise ValueError("Calibration JSON must contain a 'weights' object.")
        result = score_thumbnail(ratings, weights)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
