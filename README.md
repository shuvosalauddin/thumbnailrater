# Thumbnail Rater

Review YouTube thumbnails for clarity, small-size readability, and fit with the video title. The skill combines visual review with basic image measurements and can optionally use channel data to adjust its scoring weights.

## Install

Copy this folder to your Claude skills directory:

```text
~/.claude/skills/thumbnailrater/
```

The image-check script requires Python and Pillow:

```bash
python -m pip install Pillow
```

## Use

Ask Claude to review a thumbnail and provide the exact video title. Claude can use the guidance in `SKILL.md` and `references/` to review the image and suggest changes.

To run the image checks manually:

```bash
python scripts/prep_image.py path/to/thumbnail.jpg
```

The script reports image dimensions, aspect ratio, and grayscale tonal measurements for the original image and a small aspect-preserving preview. These measurements don't detect the subject, read text, or predict performance. Image dimensions are informational and are not penalized by the design score.

For a numeric rubric score, save the preprocessing JSON, add ratings for `subject_clarity`, `title_synergy`, and `cognitive_simplicity` (0-100), then run:

```bash
python scripts/score.py path/to/ratings.json
```

The score is a rough CTR-potential design checklist, not a predicted CTR percentage. See `references/rubric.md` for rating guidance.

## Optional calibration

`scripts/calibrate.py` accepts a CSV with impressions, CTR percentage, and human-assigned ratings for all four scoring dimensions. It does not take a raw YouTube Studio export by itself. See `references/ctr-model.md` for the required columns, example commands, and limitations.

## Contents

- `SKILL.md` — Claude skill instructions and discovery description
- `scripts/prep_image.py` — image measurements and small-preview checks
- `scripts/score.py` — combines ratings into a weighted heuristic score
- `scripts/calibrate.py` — fits optional weights from rated channel data
- `references/` — review rubric, evidence guidance, platform notes, and calibration details
