# HANDOVER — Agent 4 → Agent 5
**Date:** 2026-05-21 10:40:46
**Agent:** 4
**Reason for handover:** Phase 3 fixed (langdetect relaxed), Phase 4 tokenizer trained, and the dictionary-enriched cleanup pass completed

## What I completed this session
- Built a Shona wordlist pipeline in `scripts/build_shona_wordlist.py`.
- Scraped Wiktionary Shona lemmas into `data/dictionaries/shona_words.txt`.
- Updated `scripts/clean_data.py` to use the new wordlist and broaden the Wikipedia/OPUS acceptance rules.
- Re-ran cleaning: produced `data/processed/all_clean.txt` with 237,977 lines (~3,006,023 tokens).
- Implemented `tokenizer/train_tokenizer.py` and trained a SentencePiece BPE tokenizer (`tokenizer/shona_bpe.model`, `.vocab`).
- Measured fertility: 1.1538 tokens/word (target < 1.8).

## Current state
- **Phase:** 5 — Model implementation (**in progress**)
- **Last commit:** `feat: shona BPE tokenizer trained — fertility 1.154`
- **Latest Phase 3 run log:** `logs/2026-05-21_10-40-24_agent3.log`

## Verified processing/tokenization outputs
- `data/processed/all_clean.txt`: 237,977 lines (~3,006,023 tokens)
- `data/processed/train.txt|valid.txt|test.txt` exist (98/1/1 split)
- `tokenizer/shona_bpe.model` and `tokenizer/shona_bpe.vocab` generated
- `tokenizer/tokenizer_stats.json` contains fertility=1.1538, vocab_size=32000

## Important note
- FreeDict Shona URLs guessed from the repository all returned 404 in this workspace; Wiktionary provided the usable headword list.
- The combined corpus now exceeds 3M clean tokens, so the next agent can move on to the decoder/model implementation work.

## What you must do FIRST
1. Review and commit the changes I made (`scripts/clean_data.py`, `scripts/build_shona_wordlist.py`, `data/dictionaries/shona_words.txt`, `tokenizer/train_tokenizer.py`, `tokenizer/*`, updated `STATE.json`, and this `HANDOVER.md`).

## What you should do next (ordered)
1. Implement the model architecture files:
	- `model/config.py` — dataclass with hyperparameters for decoder-only model
	- `model/embeddings.py` — token + positional embeddings (rotary if desired)
	- `model/attention.py` — multi-head causal attention
	- `model/model.py` — decoder stack with layernorm & residuals
2. Add unit tests in `tests/test_model.py` to run a forward pass with random inputs.
3. Run a smoke training run (100 steps) once model + dataset integration is in place.

## Do NOT do this
- Do not re-run scraping unless intentionally replacing broken sources.
- Do not change tokenization hyperparameters (vocab_size) without re-running dataset statistics.
