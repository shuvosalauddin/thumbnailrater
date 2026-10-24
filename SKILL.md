---
name: thumbnailrater
description: Review thumbnail or design screenshots with a practical, CTR-oriented checklist. Accept arbitrary image dimensions; include visual ratings and actionable improvements, not a fabricated CTR forecast.
---
# Thumbnail Rater

Use this skill as a practical design checklist for thumbnail screenshots and other supplied design images. Optimize feedback for likely click appeal, but treat ratings as informed judgment rather than exact measurement.

1. Ask for the thumbnail and video title. Ask about the audience or topic if that context would change your advice. Without the title, don't score how well the two work together or give an overall score.
2. Run [`prep_image.py`](./scripts/prep_image.py) to inspect the supplied dimensions and tonal range. Accept arbitrary screenshot dimensions; the small preview preserves the original aspect ratio. Dimensions are context, not a design-quality penalty. Mention a 16:9 crop only when the user is preparing a standard YouTube thumbnail.
3. Look at the image full-size and at the aspect-preserving small preview. Use [`rubric.md`](./references/rubric.md) to rate subject clarity, title fit, and simplicity. Treat measurements as prompts for visual inspection, not definitive judgments.
4. Run [`score.py`](./scripts/score.py) with the measurements and ratings. Present the result as a rough **CTR potential (design-only) score out of 100**, not a CTR percentage. Point out what works, then suggest a few concrete edits most likely to improve click appeal.

Say which observations came from image checks and which are your visual judgment. A screenshot alone cannot establish actual CTR; do not invent a percentage. For optional channel-data calibration and its limitations, see [`ctr-model.md`](./references/ctr-model.md).
