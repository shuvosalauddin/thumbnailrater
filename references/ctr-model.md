# CTR Calibration: Scope and Limitations

`scripts/calibrate.py` fits a simple impression-weighted linear regression using per-video ratings and observed CTR. It uses non-negative coefficients with light ridge regularization, then normalizes the coefficients to scoring weights for `scripts/score.py`.

The training CSV must contain impressions, CTR percentage, and consistently assigned 0-100 ratings for subject clarity, visual contrast, title synergy, and cognitive simplicity. The YouTube Studio export alone does not contain the visual ratings; join it with a reviewed, per-video rating sheet.

Run `python scripts/calibrate.py path\to\rated_videos.csv --output path\to\calibration.json`, then pass that file to `python scripts/score.py path\to\ratings.json --weights path\to\calibration.json`.

The model has no controls for topic, title, audience, traffic source, timing, or distribution. A good fit does not establish that thumbnail design caused the observed CTR. Weights from a small or unrepresentative sample can be unstable. Treat them as descriptive channel-specific heuristics only, and do not present the output as predicted CTR.
