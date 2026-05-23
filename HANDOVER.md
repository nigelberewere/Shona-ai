# HANDOVER — Agent 13 → Agent 14

**Date:** 2026-05-23 20:05:00  
**Agent:** 13  
**Reason for handover:** Data collection, clean passes, and dataset splits regeneration completed successfully. Ready for pre-training runs.

## What I completed this session
- **VOA Shona Scraped**: Crawled all 2,064 articles across 12 paginated categories on Voice of America Shona service (`voashona.com`). Extracted 13,037 clean lines (~272k tokens).
- **OPUS Shona Harvested**: Downloaded `bible-uedin` and `CCAligned` from OPUS, extracted and filtered the Shona side against a 166,204-word super-vocabulary whitelist to prevent agglutinative/concord collisions. Extracted 132,591 clean lines (~2.10M tokens).
- **Light Corpus Cleaning Pass**: Restored the corpus and stripped `</s>` tags, removed lines <20 characters, removed morphological `chemunhu:` artifacts, eliminated exact duplicate lines, and discarded technical/noisy logs with >50% non-alphabetic characters. Retained 129,394 lines (~2.16M tokens).
- **Targeted Cleaning Pass**: Stripped URL noise, trailing ellipses (`...`), price strings (`$\d+`), parenthesized English descriptions, and sentences with >=4 consecutive English words. Net corpus contains **122,947 lines** and **2,031,740 clean tokens** (a net growth of **+32.18%** over the pre-sprint baseline!).
- **Validation & Splits**: Split the cleaned corpus (98/1/1 split) into `train.txt` (120,488 lines), `valid.txt` (1,229 lines), and `test.txt` (1,230 lines) and updated `STATE.json` and statistics.
- **Repository Updates**: Staged and committed all cleaning pass scripts, log files, statistics, and metadata.

## Current state
- **Phase:** 2 — Data Collection — Complete!
- **Total Corpus Size**: 122,947 lines, 2,031,740 clean tokens.
- **Last commit**: `fix: remove URL noise and English leakage from corpus`

---

## 🚀 RETRAINING INSTRUCTIONS FOR THE NEXT AGENT (AGENT 14)

You are tasked with running the Phase 7 model pre-training on the newly expanded **2.03M token Shona training corpus**.

### Retraining Protocol:
1. **Platform**: Execute the training run on a **Kaggle GPU environment** (or equivalent accelerator).
2. **Trainer Script**: Use `training/trainer.py` with the exact same hyperparameters and settings as utilized in the prior smoke/pilot training loops.
3. **Training Length**: Target exactly **100,000 steps** of pre-training.
4. **Expected Metric Improvement**: 
   * The validation perplexity (`val_ppl`) must drop below **651.4** (the Phase 8 perplexity baseline).
   * **Target Perplexity**: **Below 400** on the validation split.
5. **Output Checkpoint**: Save the final trained checkpoint to the following path:
   * `training/checkpoints/shona_ai_v2.pt`

*Good luck, Agent 14. The data is ready!*
