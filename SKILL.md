---
name: thumbnailrater
description: Review YouTube thumbnails for clarity, readability, and fit with the video title. Includes image checks and optional channel-data calibration.
---
# Thumbnail Rater

Use this skill to review a YouTube thumbnail and suggest practical improvements.

1. Ask for the thumbnail and video title. Ask about the audience or topic if that context would change your advice. Without the title, don't score how well the two work together or give an overall score.
2. Run [`prep_image.py`](./scripts/prep_image.py) to check the image dimensions and tonal range. These checks don't identify the subject, read text, or determine whether the thumbnail is easy to understand.
3. Look at the image full-size and at a small preview. Use [`rubric.md`](./references/rubric.md) to rate subject clarity, title fit, and simplicity. Use the measured contrast score unless your visual review suggests otherwise; explain any change.
4. Run [`score.py`](./scripts/score.py) with the measurements and ratings. Point out what works, then suggest a few concrete edits.

The score is a rough guide, not a CTR forecast. Say which observations came from the image checks and which are your visual judgment. For optional channel-data calibration, see [`ctr-model.md`](./references/ctr-model.md).
