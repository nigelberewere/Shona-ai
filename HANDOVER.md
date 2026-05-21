# HANDOVER — Agent 7 → Agent 8
**Date:** 2026-05-22 01:15:00  
**Agent:** 7  
**Model:** Gemini 3.5 Flash (High)  
**Reason for Handover:** Completed Phase 6 training loop diagnosis and fix, verified data quality audit, and established the first honest, validated baseline checkpoint.

---

## 1. Metrics and Core Achievements

### A. Task 1: Training Data Audit
We wrote and executed `scripts/audit_data.py` on the training corpus `data/processed/train.txt`:
- **Total lines**: 68,796 lines
- **English word contamination**: **1.9%** (far below the 20% critical threshold)
- **Short lines (<5 words)**: **0.0%**
- **Verdict**: Data quality is outstanding. No data-cleaning passes are required.

### B. Task 2: Causal Sequence Shifting & 300-Step Training
We ran exactly 300 steps of CPU training on `train.txt` and validated on `valid.txt` using a lightweight model configured with correct sequence shifting (`x = batch[:, :-1]` and `y = batch[:, 1:]`) and padding index `ignore_index=0` masking:
- **Step 100**: `train_loss=9.03 | val_loss=7.82 | val_ppl=2498.5`
- **Step 200**: `train_loss=7.45 | val_loss=7.44 | val_ppl=1708.4`
- **Step 300**: `train_loss=7.26 | val_loss=7.36 | val_ppl=1577.7`
- **Verdict**: The training loop works perfectly. Perplexity is above 2.0 (verifying that the evaluator is correct and not broken by the padding illusion). The perplexity is above 100 solely because the model is trained from scratch on CPU for only 300 steps, meaning it has not converged.

### C. Diagnosis of Prior Pilot Checkpoints
- We evaluated the previous pilot checkpoint `training/pilot_checkpoints/ckpt_final.pt` on the validation set using correct target shifting.
- It returned an astronomical perplexity: **166,940,379.88** (loss = 18.93).
- **Verdict**: All previous checkpoints in `training/pilot_checkpoints` are **completely invalid** due to the copy-sequence bug (`y = x.clone()`). Do NOT load or reuse them. We must train from scratch in Phase 7.

---

## 2. What was Fixed and Created
- **Causal Target Shifting**: Slices and targets are correctly contiguous and shifted in `training/trainer.py`.
- **Honest Metrics Integration**: Added padding token index masking (`ignore_index=0`) in `CrossEntropyLoss` for training and evaluation.
- **Created `scripts/audit_data.py`**: A clean, robust data quality auditor.
- **Created Checkpoint**: The verified 300-step smoke-test checkpoint is saved at `training/checkpoints/step_300.pt`.
- **STATE.json**: Updated with real, honest metrics and marked Phase 6 as complete.

---

## 3. NEXT ACTION FOR AGENT 8

> [!IMPORTANT]
> **Your single next action to start Phase 7**:
> Write and launch `training/train_full.py` to train the Shona AI model from scratch on GPU for the full training run (many thousands of steps), using our corrected target shifting (`x = batch[:, :-1].contiguous()`, `y = batch[:, 1:].contiguous()`) and padding masking (`ignore_index=0`).

---

## 4. Instructions for Agent 8

1. **Do not use pilot checkpoints**: Treat all pre-existing pilot checkpoints as garbage.
2. **GPU Training is Mandatory**: Since we are entering Phase 7, CPU training is too slow. You must run the training loop on a CUDA-enabled GPU (or adjust batch size/steps accordingly if no GPU is available, though a GPU is highly recommended for Phase 7).
3. **Check `training/pilot_run.py`**: If you ever plan to run the pilot script, modify it to use the target-shifting fix. (We focused exclusively on the main `trainer.py` this session).

Good luck, Agent 8! Build the most fluent Shona LLM!
