"""Fit non-negative scoring weights from thumbnail ratings and CTR observations."""

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


FEATURES = (
    "subject_clarity",
    "visual_contrast",
    "title_synergy",
    "cognitive_simplicity",
)
REQUIRED_COLUMNS = ("impressions", "ctr_percentage", *FEATURES)


def calibrate_weights(csv_path: str | Path) -> dict[str, Any]:
    rows = []
    with Path(csv_path).open(mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError("CSV must have a header row.")
        missing = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")

        for line_number, row in enumerate(reader, start=2):
            try:
                impressions = float(row["impressions"])
                ctr = float(row["ctr_percentage"])
                features = [float(row[feature]) / 100 for feature in FEATURES]
            except (OverflowError, TypeError, ValueError) as error:
                raise ValueError(f"Invalid numeric value on CSV line {line_number}.") from error
            if (
                not all(math.isfinite(value) for value in [impressions, ctr, *features])
                or impressions <= 0
                or not 0 <= ctr <= 100
                or any(not 0 <= feature <= 1 for feature in features)
            ):
                raise ValueError(
                    f"CSV line {line_number}: impressions must be positive and CTR/ratings must be in range."
                )
            rows.append((impressions, ctr, features))

    if not rows:
        raise ValueError("CSV has no data rows to calibrate.")

    total_impressions = sum(row[0] for row in rows)
    if not math.isfinite(total_impressions):
        raise ValueError("Total impressions must be finite.")
    sample_weights = [row[0] / total_impressions for row in rows]
    target = [row[1] for row in rows]
    feature_rows = [row[2] for row in rows]
    intercept = sum(weight * ctr for weight, ctr in zip(sample_weights, target))
    coefficients = [0.0] * len(FEATURES)
    learning_rate = 0.1
    ridge_strength = 0.01

    for _ in range(20_000):
        predictions = [
            intercept + sum(coefficient * feature for coefficient, feature in zip(coefficients, features))
            for features in feature_rows
        ]
        residuals = [prediction - actual for prediction, actual in zip(predictions, target)]
        intercept_gradient = 2 * sum(weight * error for weight, error in zip(sample_weights, residuals))
        coefficient_gradients = [
            2
            * (
                sum(
                    weight * error * features[index]
                    for weight, error, features in zip(sample_weights, residuals, feature_rows)
                )
                + ridge_strength * coefficient
            )
            for index, coefficient in enumerate(coefficients)
        ]
        next_intercept = intercept - learning_rate * intercept_gradient
        next_coefficients = [
            max(0.0, coefficient - learning_rate * gradient)
            for coefficient, gradient in zip(coefficients, coefficient_gradients)
        ]
        change = abs(next_intercept - intercept) + sum(
            abs(new - old) for new, old in zip(next_coefficients, coefficients)
        )
        intercept, coefficients = next_intercept, next_coefficients
        if change < 1e-9:
            break

    coefficient_sum = sum(coefficients)
    if coefficient_sum == 0:
        raise ValueError("The observed CTR data did not support positive weights for any rating dimension.")
    normalized_weights = {
        feature: round(coefficient / coefficient_sum, 6)
        for feature, coefficient in zip(FEATURES, coefficients)
    }
    predictions = [
        intercept + sum(coefficient * feature for coefficient, feature in zip(coefficients, features))
        for features in feature_rows
    ]
    weighted_rmse = math.sqrt(
        sum(weight * (prediction - actual) ** 2 for weight, prediction, actual in zip(sample_weights, predictions, target))
    )

    return {
        "weights": normalized_weights,
        "training": {
            "videos": len(rows),
            "total_impressions": round(total_impressions),
            "impression_weighted_average_ctr_percentage": round(
                sum(weight * ctr for weight, ctr in zip(sample_weights, target)), 3
            ),
            "weighted_rmse_ctr_percentage_points": round(weighted_rmse, 3),
            "ctr_intercept_percentage": round(intercept, 3),
            "method": "impression-weighted linear fit with non-negative coefficients and light ridge regularization",
        },
        "limitations": [
            "CTR is observational and is affected by topic, audience, traffic source, title, and distribution.",
            "Treat weights as a channel-specific heuristic, not causal evidence or a reliable CTR forecast.",
            "Ratings must be applied consistently; a small or non-representative sample can produce unstable weights.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", help="CSV with impressions, CTR, and four 0-100 rating columns")
    parser.add_argument("-o", "--output", help="Write calibration JSON to this file instead of stdout")
    args = parser.parse_args()
    try:
        result = calibrate_weights(args.csv)
        output = json.dumps(result, indent=2)
        if args.output:
            Path(args.output).write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
