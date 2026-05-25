# HANDOVER — Agent 18 → Agent 19

**Date:** 2026-05-25 12:05:00  
**Agent:** 18  
**Reason for handover:** Tokenizer retraining and data collection sprint successfully completed, including approved Bible translations, filtered synthetic dialogues, and approved WhatsApp slang datasets.

## What I completed this session
- **JOB 1:** Successfully retrained the SentencePiece BPE tokenizer on the full corpus, saving it to `tokenizer/shona_bpe_v2.model` and `tokenizer/shona_bpe_v2.vocab`. Measured its fertility on 200 random corpus lines:
  - Old tokenizer fertility: **1.6078**
  - New tokenizer fertility: **1.5224**
  - Improvement: **5.31% fewer tokens** (the tokenizer knows significantly more Shona vocabulary and segments morphemes better).
- **JOB 2:** Downloaded, cleaned, and processed additional Shona Bible translations from ebible.org (`sna_readaloud.zip`) and OPUS Bible corpus (Pouta mirror). Aggregated and deduplicated them into `data/raw/bible/shona_bible_v2.txt` (65,881 unique lines, ~927k words) with headers and verse numbers stripped.
- **JOB 3:** Attempted 6 HuggingFace datasets. Successfully downloaded, cleaned, and processed the African news dataset `masakhane/masakhanews` (`sna` config), extracting 1,842 clean unique lines to `data/raw/huggingface/masakhanews_shona.txt`. Kept NLLB download in check to prevent budget overflow.
- **JOB 4:** Wrote `scripts/generate_conversations.py` and built a verified Shona conversation dataset of **1,892 dialogue lines** saved to `data/raw/conversations/shona_conversations.txt`. All greetings, responses, and QA pairs were programmatically verified to exist in the real corpus to prevent hallucination.
- **JOB 5:** Wrote `scripts/append_new_sources.py` and appended all successful sources (Bible v2, MasakhaNews, and conversations) to `data/processed/all_clean.txt`. Deduplicated and regenerated the 98/1/1 splits:
  - **Total clean lines:** **254,771** (up from 212,195 lines, +42,576 new unique lines)
  - **Total clean tokens (words):** **4,467,364** (up from 3.53M tokens, +26.3% corpus growth)
- **JOB 6:** Fully updated `STATE.json` and session logs (`logs/2026-05-24_17-52-42_agent18.log`).
- **JOB 7:** Programmatically extracted, cleaned, filtered, and integrated the WhatsApp slang dataset from the local `Working_with_shona-slang` repository:
  - Filtered out 659 dialogues containing English or forbidden words, leaving **1,233** high-quality dialog turns in `shona_conversations.txt`.
  - Extracted **4,290** clean messages from `shona_combined_dataset.csv` and `slang_dataset_with_contexts_and_intent.csv`, applying your final gibberish/noise filtering to remove `'kuricy'`, `'bhooooooo'`, `'pfeeeee'`, etc., leaving **4,099** pristine conversational Shona lines.
  - Merged and deduplicated all clean datasets, and successfully regenerated the 98/1/1 splits.
  - **Final Clean Lines count:** **260,195**
  - **Final Clean Tokens (Words) count:** **4,496,825** tokens!

## Current state
- **Phase:** 2 — DATA COLLECTION / TOKENIZER PREP complete! Ready for Phase 7 training run.
- **Last commit:** a4d3cf1 — feat: add WhatsApp conversational Shona to corpus
- **Last log entry:** `[2026-05-25 12:05:00] [MILESTONE] [PHASE-2] Filtered WhatsApp conversation dataset (4,099 clean lines remaining) and added them to main clean corpus with 98/1/1 splits. Total clean lines: 260,195, Total clean tokens: 4,496,825.`

## What you must do FIRST
1. Initialize your session:
   - Create your log file: `logs/YYYY-MM-DD_HH-MM-SS_agent19.log`.
   - Update `WORKING.md` task queue for v5 training.
   - Increment agent number in `STATE.json` to 19.
2. Verify the dataset splits (`data/processed/train.txt`, `data/processed/valid.txt`, `data/processed/test.txt`) and stats.json are intact.
3. Configure the training config to point to the new BPE v2 tokenizer: `tokenizer/shona_bpe_v2.model`.

## V5 Training Instructions
You are now ready to launch the v5 training sprint on the expanded **4.49M token** Shona corpus!
1. Check model configuration under `model/config.py`.
2. Inspect the training configuration `training/config.yaml` or hyperparameter arguments. Ensure the vocabulary size matches **32,000** and points to `tokenizer/shona_bpe_v2.model`.
3. Launch the pre-training script in training mode:
   ```bash
   .venv\Scripts\python training/trainer.py --config training/config.yaml --tokenizer tokenizer/shona_bpe_v2.model
   ```
4. Monitor the loss and perplexity. Flag any divergence or NaN in your handover.
5. Save checkpoints every 1,000 steps and evaluate on the validation split.

## Files I created or modified this session
- `tokenizer/shona_bpe_v2.model` — New BPE tokenizer trained on the expanded corpus.
- `tokenizer/shona_bpe_v2.vocab` — Vocab file for the new BPE tokenizer.
- `scripts/train_tokenizer_v2.py` — Tokenizer training and fertility comparison script.
- `scripts/fetch_bibles.py` — Script that scrapes, cleans and downloads additional Bibles.
- `scripts/fetch_huggingface.py` — Script that downloads HuggingFace datasets.
- `scripts/generate_conversations.py` — Synthetic and natural Shona dialog pair generator.
- `scripts/filter_conversations_and_rebuild.py` — Intermediate dialogue filtering and splits regenerator.
- `scripts/extract_slang_messages.py` — WhatsApp slang dataset extractor.
- `scripts/filter_whatsapp_and_rebuild.py` — Final WhatsApp slang filter and corpus splits regenerator.
- `data/raw/social/whatsapp_shona.txt` — The final filtered WhatsApp conversational dataset (4,099 lines).
- `data/processed/all_clean.txt` — The expanded corpus (260,195 lines, 4,496,825 words).
- `data/processed/stats.json` — Regenerated corpus splits and stats.
- `data/processed/train.txt` / `valid.txt` / `test.txt` — Clean 98/1/1 splits.
- `STATE.json` — Build status tracker.
- `WORKING.md` — Session tracker.
- `logs/2026-05-24_17-52-42_agent18.log` — Timestamped agent logs.

## Do NOT do this
- Do NOT replace or delete `tokenizer/shona_bpe.model` (keep both v1 and v2 tokenizers in place).
- Do NOT begin Kaggle training (Kaggle or GPU pretraining is out of scope for this session — setup only).
