# Shona AI — Progress Log

This file is append-only. Each agent adds a timestamped session summary at the end of the file.

## 2026-05-21 — Agent 5

- Implemented minimal decoder model files and unit tests. Forward-pass test passed.
- Ran 100-step smoke training on synthetic data; loss decreased (8.3925 → 7.3613). Checkpoint saved locally.

## 2026-05-21 — Agent 5 (pilot)

- Ran 1,000-step pilot training on a 256-sample tokenized slice from `data/processed/train.txt`; final loss=0.0159, avg_loss~1.2118. Checkpoint: `training/checkpoint_real_smoke.pt`.

## 2026-05-22 — GitHub Copilot

- Current agent: GitHub Copilot using GPT-5.4 mini.
- Completed data cleanup hardening in `scripts/clean_data.py`, including stronger structural/system/dictionary filters, explicit sentence boundary handling, and an ultra-strict whitelist pass to reduce contamination.
- Rebuilt processed splits multiple times and validated that the cleaned corpus still produced usable training data after the stricter pass.
- Retrained the smoke model from scratch with `python -m training.trainer 5000`; checkpoint saved at `training/checkpoint_real_smoke.pt`.
- Ran a focused sampling sweep, then a narrower sweep around the best combo. The best observed setting moved to temp=1.8, top_k=50, rep_pen=1.6, top_p=None with repetition_score 0.0241, a marked improvement over earlier runs.
- Successes: the retrain completed cleanly, the inference pipeline was adjusted to load the new checkpoint, and the sampling metric improved materially after the narrower sweep.
- Current work: preparing a supervisor update and evaluating whether the current winner should be confirmed with a small follow-up sweep or promoted as the default sampling setting.
- Challenges: some generated samples still show subword collisions, odd token joins, and residual contamination-like fragments, so the quality signal is better but not fully clean across every prompt.

