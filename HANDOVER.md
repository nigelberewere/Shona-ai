# HANDOVER — Agent 16 → Agent 17

**Date:** 2026-05-24 14:40:00  
**Agent:** 16  
**Reason for handover:** O-Level Shona study materials and Tambaoga Mwanangu novel successfully integrated, splits regenerated (98/1/1), and files committed. Model ready for Kaggle GPU Phase 3 pre-training.

## What I completed this session
- **O-Level Study Materials Extraction & Integration**:
  - Successfully extracted clean Shona text from PDF and DOCX files in `data/raw/SHONA/` (including grammar books, proverbs, and cultural notes).
  - Ignored scanned OCR-locked PDFs (e.g. `Mazita emadunhurirwa pdf.pdf` and `O_level_Dudziramutauro_reChishona.pdf`) and password-protected files (e.g. `Ngatidzidzei ChiShona F4 textbook 2019.pdf`).
  - Shown raw extraction samples and validated readable, high-quality native Shona sentences.
- **Shona Novel Integration**:
  - Located, parsed, and lightly cleaned the classic Shona novel `Tambaoga Mwanangu.txt` (under `data/raw/novels/`).
  - Removed blank lines and lines < 15 characters, removed empty/short chapter headers (e.g., `CHITSAUKO 5:`), and preserved the actual narrative prose.
  - Merged **241 highly clean lines** and **11,760 words (~13,523 subword tokens)** of premium native prose into the main training corpus with zero English leakage or technical noise.
- **Splits & Statistics**:
  - Shuffled and regenerated 98/1/1 splits:
    - `train.txt`: 207,931 lines (3,468,619 tokens)
    - `valid.txt`: 2,121 lines (35,394 tokens)
    - `test.txt`:  2,121 lines (35,394 tokens)
  - Updated `STATE.json` and `data/processed/stats.json` to record final gold corpus size of **212,173 unique clean lines** and **3,539,407 clean tokens**.
  - All extraction and cleaning scripts (`scripts/extract_study_materials.py`, `scripts/clean_and_filter_study_materials.py`, and `scripts/clean_and_add_novel.py`) have been added to git.

## Current state
- **Phase:** 2 — Data Collection — Complete!
- **Total Gold Baseline Corpus Size**: 212,173 lines, **3,539,407 clean tokens**.
- **Last commit**: `feat: add first novel to corpus`

---

## 🚀 RETRAINING INSTRUCTIONS FOR THE NEXT AGENT (AGENT 17)

You are tasked with running the pre-training loop on the expanded **3.53M token** Shona training corpus.

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

*Good luck, Agent 17. The Shona Gold corpus is fully prepared, expanded, and optimized with premium literature!*
