# Shona AI Progress Report

**Date:** 2026-05-22  
**Agent:** GitHub Copilot  
**Model:** GPT-5.4 mini

## Purpose

This report captures what has been completed so far, what worked well, what remains in progress, and the current blockers or quality risks. It is written for supervisor review and is intentionally explicit so the full state of the work is clear without needing additional context.

## What Has Been Done

### Data cleanup and contamination reduction

- Hardened `scripts/clean_data.py` to remove contamination that was causing repeated tokens, degenerate loops, and poor generation quality.
- Expanded structural rejection patterns so that wiki boilerplate, system-log-like text, dictionary fragments, and similar non-corpus material are filtered more aggressively.
- Strengthened sentence-shape and dictionary-entry heuristics so short fragments, list-like entries, and low-signal lines are rejected more reliably.
- Added explicit `</s>` boundary handling in the cleaned outputs so the processed corpus has clearer sequence termination.
- Introduced an ultra-strict whitelist pass to test whether even more aggressive cleanup would improve generation stability.
- Rebuilt the processed corpus multiple times after each cleanup change and validated that the resulting splits were still usable for training.

### Training

- Ran a from-scratch smoke retraining pass with `python -m training.trainer 5000`.
- The training run completed successfully and saved a new checkpoint at `training/checkpoint_real_smoke.pt`.
- Training loss dropped sharply over the run, showing the model was learning from the cleaned corpus rather than collapsing or failing to converge.

### Inference and sampling evaluation

- Updated the focused sampling evaluation path so it loads the new smoke checkpoint instead of the older pilot checkpoint.
- Fixed model-loading shape mismatch handling in `inference/sampling_sweep.py` so the checkpoint can be loaded into the inference configuration safely.
- Ran a focused sweep around the current best settings to compare temperature, top-k, top-p, and repetition penalty combinations.
- Ran a narrower second sweep around the strongest configuration to refine the final sampling hyperparameters.
- Wrote the results to `logs/focused_sweep_results.txt` and the ranked best samples to `logs/focused_sweep_best.txt`.

### Reporting and tracking

- Updated `PROGRESS.md` with a supervisor-facing status note.
- Marked the cleaning, retraining, and sweep tasks as completed in the task tracker.

## What Agent I Am

I am GitHub Copilot running as GPT-5.4 mini.

## Successes Encountered

- The data contamination issue was reduced materially after the cleanup hardening pass.
- The training pipeline worked end to end once the retrain was launched with the correct module invocation.
- The smoke checkpoint was produced successfully and used for inference without breaking the workflow.
- The sampling pipeline showed a strong improvement after the cleaner data and the retrain.
- The best observed repetition score improved substantially during the narrowing sweeps.
- The final narrow sweep found a stronger sampling configuration than the earlier passes, showing the retrain plus cleanup changes were directionally correct.

## Current State

- The cleaned corpus has been rebuilt and the smoke model has been retrained.
- The focused sampling sweep has been run against the new checkpoint.
- The current best observed sampling setting is:
  - temperature: 1.8
  - top_k: 50
  - repetition_penalty: 1.6
  - top_p: None
- The best observed repetition score in the latest narrow sweep is 0.0241.
- The inference scripts now point at the new checkpoint and can load it correctly.

## What I Am Doing Now

- Preparing a clear supervisor-ready summary of the completed work and the remaining risk.
- Reviewing whether the current best sampling setting should be accepted as the default or confirmed with one more small validation sweep.
- Watching for any remaining signs of contamination, token-joining artifacts, or repetitive subword loops in generated samples.

## Challenges We Are Facing

- Some generated samples still contain odd token joins, subword collisions, and occasional contamination-like fragments.
- The cleaned corpus is better, but the signal is not perfectly clean across every prompt.
- The quality metric improved, but it is still based on a small prompt set, so it may not fully represent broader generation behavior.
- The ultra-strict cleaning pass removed too much signal in some earlier tests, so there is a tradeoff between cleanliness and preserving useful training text.
- The sweep runs are computationally expensive enough that the narrower evaluation still takes several minutes.

## Key Artifacts

- [scripts/clean_data.py](scripts/clean_data.py)
- [inference/focused_sweep.py](inference/focused_sweep.py)
- [inference/sampling_sweep.py](inference/sampling_sweep.py)
- [training/trainer.py](training/trainer.py)
- [training/checkpoint_real_smoke.pt](training/checkpoint_real_smoke.pt)
- [logs/focused_sweep_results.txt](logs/focused_sweep_results.txt)
- [logs/focused_sweep_best.txt](logs/focused_sweep_best.txt)
- [PROGRESS.md](PROGRESS.md)

## Summary

The main goal so far has been to remove contaminated training data, retrain a clean smoke model, and verify that the model generates less repetitive text. That workflow is now complete end to end. The current best sampling configuration is clearly better than the earlier settings, but the outputs still are not perfect, so the remaining work is about confirming stability and deciding whether another small refinement pass is worth the extra time.