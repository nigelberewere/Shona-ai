# WORKING — Agent 18

**RIGHT NOW:** JOB 6 — Update STATE.json, HANDOVER.md and final commit.

## Task queue for this session

- [x] JOB 1: Retrain the SentencePiece tokenizer on the full corpus (`shona_bpe_v2.model`) and measure/compare fertility.
- [x] JOB 2: Find, scrape, clean and download additional Shona Bible translations from ebible.org, Christos, Bible Gateway, and OPUS. Save to `data/raw/bible/shona_bible_v2.txt`.
- [x] JOB 3: Check and download additional HuggingFace datasets (`opus_books`, `opus-100`, `flores`, `nllb`, `ccmatrix`, `masakhanews`).
- [x] JOB 4: Create a synthetic Shona conversation dataset using only verified Shona vocabulary. Write `scripts/generate_conversations.py`.
- [x] JOB 5: Append new datasets to `data/processed/all_clean.txt`, regenerate 98/1/1 splits, and report final corpus counts.
- [ ] JOB 6: Update `STATE.json`, `HANDOVER.md` and commit with message "feat: v5 prep - retrain tokenizer and data collection".

## Completed this session

| Time | Task | File | Commit hash |
|------|------|------|-------------|
| 18:05 | JOB 1: Retrained SentencePiece BPE tokenizer on full corpus and measured fertility | tokenizer/shona_bpe_v2.model, tokenizer/shona_bpe_v2.vocab, scripts/train_tokenizer_v2.py | 07a7e82 |
| 18:08 | JOB 2: Fetched, cleaned, and deduplicated additional Shona Bible translations (65,881 unique lines) | data/raw/bible/shona_bible_v2.txt, scripts/fetch_bibles.py | 636c9e0 |
| 18:23 | JOB 3: Attempted 6 HuggingFace datasets, successfully collected and cleaned MasakhaNews (1,842 unique lines) | data/raw/huggingface/masakhanews_shona.txt, scripts/fetch_huggingface.py | dfea9ca |
| 18:33 | JOB 4: Created a synthetic Shona conversation dataset (1,892 dialogue lines) using verified corpus vocabulary | data/raw/conversations/shona_conversations.txt, scripts/generate_conversations.py | [to be committed] |
| 18:43 | JOB 5: Appended all successful sources to clean corpus, deduplicated, and regenerated 98/1/1 splits (Total: 4.46M words) | data/processed/all_clean.txt, stats.json, splits, scripts/append_new_sources.py | [to be committed] |
