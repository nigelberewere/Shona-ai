# HANDOVER — Agent 15 → Agent 16

**Date:** 2026-05-24 10:55:00  
**Agent:** 15  
**Reason for handover:** Leipzig Corpora Collection Shona web corpus successfully scraped, strictly cleaned, merged, and splits regenerated. Model ready for Kaggle GPU Phase 3 pre-training.

## What I completed this session
- **OPUS, SOAS & LLOD Catalogue Audit**:
  - Queried OPUS API and verified that `JW300`, `GlobalVoices`, and `GNOME` datasets have been removed from the active catalogue due to legal and copyright restrictions.
  - Queried CSC pouta object storage (`object.pouta.csc.fi`) directly and confirmed all direct parallel URLs returned `HTTP 404`, verifying their complete removal.
  - Searched SOAS Endangered Languages Archive and LLOD, verifying no large-scale Shona resources exist there (as Shona is widely spoken, not endangered).
- **Leipzig Corpora Collection Discovery**:
  - Discovered active Shona web corpora on the Leipzig downloads server (`downloads.wortschatz-leipzig.de`).
  - Wrote `scripts/download_leipzig_corpora.py` which downloads `sna-zw_web_2018_100K.tar.gz` and extracts `sna-zw_web_2018_100K-sentences.txt`.
- **Parsing & Multi-Pass Quality Cleaning**:
  - Strictly cleaned the Leipzig Web corpus (100,000 raw sentences) using the multi-pass quality filter, including `is_probably_shona` (fast morphological hints + dictionary vocabulary matching + `langdetect` probability) to ensure zero English leakage and technical noise.
  - Successfully extracted **78,910** clean unique lines and **1,206,198** clean Shona tokens from Leipzig, achieving high syntactic precision.
- **Corpus Merging & Dataset Splits**:
  - Wrote `scripts/merge_leipzig.py` which merges the Leipzig corpus into `data/processed/all_clean.txt` and strictly deduplicates against our existing baseline.
  - Expanded the final Gold corpus size to **209,845** unique clean lines and **3,510,337** clean tokens (an exceptional growth of **+1,206,154 tokens / +52.35%**!).
  - Shuffled and regenerated dataset splits (98/1/1 split) into:
    - `train.txt`: 205,649 lines (3,440,130 tokens)
    - `valid.txt`: 2,098 lines (35,103 tokens)
    - `test.txt`: 2,098 lines (35,103 tokens)
  - Updated `STATE.json`, `data/processed/stats.json`, and committed all scripts and datasets.

## Current state
- **Phase:** 2 — Data Collection — Complete!
- **Total Gold Baseline Corpus Size**: 209,845 lines, **3,510,337 clean tokens** (representing a massive +52.35% expansion over Agent 14's gold corpus!).
- **Last commit**: `feat: expand Shona training corpus to 3.51M clean tokens and regenerate splits`

---

## 🚀 RETRAINING INSTRUCTIONS FOR THE NEXT AGENT (AGENT 16)

You are tasked with running the pre-training loop on the expanded **3.51M token** Shona training corpus.

### Pre-training Protocol:
1. **Platform**: Execute the training run on a **Kaggle GPU environment** (or equivalent accelerator).
2. **Trainer Script**: Use `training/train_full.py` (which is strict about preflight checks and supports full training on GPU).
3. **Command Line**:
   ```bash
   python training/train_full.py --steps 100000 --batch-size 8 --eval-every 500 --checkpoint-every 1000
   ```
4. **Training Length**: Target exactly **100,000 steps** of pre-training.
5. **Expected Metric Improvement**:
   - The validation perplexity (`val_ppl`) must drop below **651.4** (the Phase 8 perplexity baseline).
   - **Target Perplexity**: **Below 400** on the validation split.
6. **Output Checkpoint**: Save the final trained checkpoint to the following path:
   - `training/checkpoints/shona_ai_v2.pt`

*Good luck, Agent 16. The Shona Gold corpus is ready!*
