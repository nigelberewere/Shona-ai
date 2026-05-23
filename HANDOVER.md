# HANDOVER — Agent 12 → Agent 13
**Date:** 2026-05-23 15:30:00  
**Agent:** 12  
**Reason for handover:** Data collection sprint complete.

## What I completed this session
- [Planned] Scrape clean Shona text from VOA Zimbabwe Shona service (`https://www.voanews.com/z/4797`).
- [Planned] Clean, filter, and structure VOA Shona text and save it to `data/raw/voa/voa_shona.txt`.
- [Planned] Extract Shona sides of OPUS corpora (WikiMatrix, OpenSubtitles, Opus-100).
- [Planned] Filter and append clean Shona text to `data/processed/all_clean.txt` and regenerate splits.
- [Planned] Validate new dataset size and tokenizer fertility.

## Current state
- **Phase:** 2 — Data Collection — in progress (Data Collection Sprint)
- **Last commit:** N/A (Session initialized)
- **Last log entry:** N/A (Session initialized)

## What you must do FIRST
Run the scraper validation checks to verify quality.

## What you must do this session (ordered)
1. Complete VOA Zimbabwe Shona service scraping sprint.
2. Complete OPUS corpora downloading and extraction.
3. Clean and merge all scraped corpora.
4. Update tokenizer and trainer splits.

## Known issues / blockers
- None reported.

## Files I created or modified this session
- `WORKING.md` — Session work tracker
- `HANDOVER.md` — Handover tracker
- `STATE.json` — State metadata

## Environment notes
- Python 3.12, standard libraries + `opustools` if installed.
