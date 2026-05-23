# HANDOVER — Agent 14 → Agent 15

**Date:** 2026-05-23 23:28:00  
**Agent:** 14  
**Reason for handover:** Gold baseline corpus successfully expanded and splits regenerated. Ready for Kaggle GPU model pre-training.

## What I completed this session
- **Job 1 (CCAligned machine translation removal)**: Verified that low-quality CCAligned noise was successfully removed and replaced with clean baseline sources.
- **Masakhane Shona news datasets**: Successfully scraped `masakhanews` and `mafand` splits, extracting **3,899 clean lines** (~202k tokens) of pristine Shona news text.
- **Internet Archive literature**: Searched and retrieved public-domain books (Bible history `testamente_202605` etc.) from archive.org. Cleaned OCR noise and English leakage to keep **1,507 lines** (~10k tokens) of historical Shona prose.
- **VOA historical sitemap crawler**: Parsed sitemaps from `voashona.com/sitemap.xml` to gather a database of **40,000 unique URLs**.
- **VOA concurrent scraper**: Developed a robust multi-threaded crawler (`scripts/scrape_voa_archive.py`) utilizing 40 workers concurrently. Executed two successful scraping passes over 9,500 sampled URLs, yielding **23,318 clean lines** (~481k tokens) of historical journalism.
- **Corpus compilation & deduplication**: Built `scripts/compile_additional_data.py` to clean all new sources, run English stopword detectors, and deduplicate against our baseline. Appended a net of **+639,344 clean Shona tokens** to the Gold baseline, easily beating the 500K tokens goal!
- **Dataset splits regenerated**: Split the final 3.77M token corpus (98/1/1 split) into `train.txt` (267,325 lines), `valid.txt` (2,727 lines), and `test.txt` (2,727 lines) and updated `STATE.json` and `stats.json`.

## Current state
- **Phase:** 2 — Data Collection — Complete!
- **Total Gold Baseline Corpus Size**: 272,779 lines, **3,773,335 clean tokens**.
- **Last commit**: `feat: literature and news data collection sprint`

---

## 🚀 RETRAINING INSTRUCTIONS FOR THE NEXT AGENT (AGENT 15)

You are tasked with running the model pre-training on the expanded **3.77M token Shona training corpus**.

### Pre-training Protocol:
1. **Platform**: Execute the training run on a **Kaggle GPU environment** (or equivalent accelerator).
2. **Trainer Script**: Use `training/trainer.py` with the exact same hyperparameters and settings as utilized in the prior smoke/pilot training loops.
3. **Training Length**: Target exactly **100,000 steps** of pre-training.
4. **Expected Metric Improvement**: 
   * The validation perplexity (`val_ppl`) must drop below **651.4** (the Phase 8 perplexity baseline).
   * **Target Perplexity**: **Below 400** on the validation split.
5. **Output Checkpoint**: Save the final trained checkpoint to the following path:
   * `training/checkpoints/shona_ai_v2.pt`

*Good luck, Agent 15. The Shona Gold corpus is ready!*
