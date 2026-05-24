# WORKING — Agent 18

**RIGHT NOW:** JOB 4 — Build synthetic Shona conversation dataset.

## Task queue for this session

- [x] JOB 1: Retrain the SentencePiece tokenizer on the full corpus (`shona_bpe_v2.model`) and measure/compare fertility.
- [x] JOB 2: Find, scrape, clean and download additional Shona Bible translations from ebible.org, Christos, Bible Gateway, and OPUS. Save to `data/raw/bible/shona_bible_v2.txt`.
- [x] JOB 3: Check and download additional HuggingFace datasets (`opus_books`, `opus-100`, `flores`, `nllb`, `ccmatrix`, `masakhanews`).
- [ ] JOB 4: Create a synthetic Shona conversation dataset using only verified Shona vocabulary. Write `scripts/generate_conversations.py`.
- [ ] JOB 5: Append new datasets to `data/processed/all_clean.txt`, regenerate 98/1/1 splits, and report final corpus counts.
- [ ] JOB 6: Update `STATE.json`, `HANDOVER.md` and commit with message "feat: v5 prep - retrain tokenizer and data collection".

## Completed this session

| Time | Task | File | Commit hash |
|------|------|------|-------------|
| 18:05 | JOB 1: Retrained SentencePiece BPE tokenizer on full corpus and measured fertility | tokenizer/shona_bpe_v2.model, tokenizer/shona_bpe_v2.vocab, scripts/train_tokenizer_v2.py | 07a7e82 |
| 18:08 | JOB 2: Fetched, cleaned, and deduplicated additional Shona Bible translations (65,881 unique lines) | data/raw/bible/shona_bible_v2.txt, scripts/fetch_bibles.py | 636c9e0 |
| 18:23 | JOB 3: Attempted 6 HuggingFace datasets, successfully collected and cleaned MasakhaNews (1,842 unique lines) | data/raw/huggingface/masakhanews_shona.txt, scripts/fetch_huggingface.py | [to be filled or committed] |
