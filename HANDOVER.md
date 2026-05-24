# HANDOVER — Agent 18 → Agent 19

**Date:** 2026-05-24 17:52:42  
**Agent:** 18  
**Reason for handover:** Tokenizer retraining + data collection sprint in progress.

## What I completed this session
- Session initialized and planned.

## Current state
- **Phase:** 2 — DATA COLLECTION / TOKENIZER PREP
- **Last commit:** d86e645 — feat: social media and web scraping sprint

## What you must do FIRST
- Retrain the SentencePiece tokenizer on the full corpus.

## What you must do this session (ordered)
1. JOB 1: Retrain the SentencePiece tokenizer on the full corpus (`shona_bpe_v2.model`) and measure/compare fertility.
2. JOB 2: Find, scrape, clean and download additional Shona Bible translations from ebible.org, Christos, Bible Gateway, and OPUS. Save to `data/raw/bible/shona_bible_v2.txt`.
3. JOB 3: Check and download additional HuggingFace datasets (`opus_books`, `opus-100`, `flores`, `nllb`, `ccmatrix`, `masakhanews`).
4. JOB 4: Create a synthetic Shona conversation dataset using only verified Shona vocabulary. Write `scripts/generate_conversations.py`.
5. JOB 5: Append new datasets to `data/processed/all_clean.txt`, regenerate 98/1/1 splits, and report final corpus counts.
6. JOB 7: Update `STATE.json`, `HANDOVER.md` and commit with message "feat: v5 prep - retrain tokenizer and data collection".
