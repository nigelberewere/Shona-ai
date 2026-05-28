# HANDOVER — Agent 18 → Agent 19

**Date:** 2026-05-28 18:55:00  
**Agent:** 18  
**Reason for handover:** Tokenizer retraining, slang data collection, and custom model architecture upgrade for v6 training loop successfully completed!

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
- **JOB 6:** Fully updated `STATE.json` and session logs.
- **JOB 7:** Programmatically extracted, cleaned, filtered, and integrated the WhatsApp slang dataset from the local `Working_with_shona-slang` repository:
  - Filtered out 659 dialogues containing English or forbidden words, leaving **1,233** high-quality dialog turns in `shona_conversations.txt`.
  - Extracted **4,290** clean messages from `shona_combined_dataset.csv` and `slang_dataset_with_contexts_and_intent.csv`, applying your final gibberish/noise filtering to remove `'kuricy'`, `'bhooooooo'`, `'pfeeeee'`, etc., leaving **4,099** pristine conversational Shona lines.
  - Merged and deduplicated all clean datasets, and successfully regenerated the 98/1/1 splits.
  - **Final Clean Lines count:** **260,195**
  - **Final Clean Tokens (Words) count:** **4,496,825** tokens.
- **JOB 8:** Upgraded the custom causal GPT model architecture defaults in `model/config.py` and `training/trainer.py` to support v6 large pre-training on Kaggle:
  - **Hidden Size:** 256 (up from 128)
  - **Attention Heads:** 8
  - **Layers:** 6 (up from 2)
  - **Intermediate Size:** 1024 (up from 512)
  - **Max Position Embeddings:** 256
  - **Steps:** 100,000 steps
  - **Batch Size:** 32 (up from 4)
  - **Learning Rate:** 1e-3 (AdamW)
  - **Max Train / Val samples:** None (full corpus training!)
  - Verified exact parameter count of the new architecture: **21,188,608 parameters** (model size: **80.8 MB**).

## Current state
- **Phase:** 2 — DATA COLLECTION / TOKENIZER PREP complete! Ready for Phase 7 training run.
- **Last commit:** 9d2b952 — feat: configure trainer.py with hidden=256 layers=6 for Kaggle training run
- **Last log entry:** `[2026-05-25 12:05:00] [MILESTONE] [PHASE-2] Filtered WhatsApp conversation dataset (4,099 clean lines remaining) and added them to main clean corpus with 98/1/1 splits. Total clean lines: 260,195, Total clean tokens: 4,496,825.`

## What you must do FIRST
1. Initialize your session:
   - Create your log file: `logs/YYYY-MM-DD_HH-MM-SS_agent19.log`.
   - Update `WORKING.md` task queue for v6 training.
   - Increment agent number in `STATE.json` to 19.
2. Verify the dataset splits (`data/processed/train.txt`, `data/processed/valid.txt`, `data/processed/test.txt`) and stats.json are intact.
3. Configure the training config to point to the BPE v2 tokenizer: `tokenizer/shona_bpe_v2.model`.

## V6 Training Instructions
You are now ready to launch the v6 training sprint on Kaggle using the upgraded **21.1M parameter** Shona model!
1. Set up your Kaggle notebook, loading the `Shona-ai` repository.
2. Ensure you have the `shona_bpe_v2.model` and the clean train/val datasets loaded.
3. Launch the pre-training script in training mode:
   ```bash
   python training/trainer.py
   ```
4. Monitor the loss and perplexity. Flag any divergence or NaN in your handover.
5. Save checkpoints every 1,000 steps and evaluate on the validation split.

## Files I created or modified this session
- `model/config.py` — Upgraded default ModelConfig to 21.1M parameters.
- `training/trainer.py` — Upgraded trainer configuration defaults, batch size, steps and learning rate for Kaggle v6 training.
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
- Do NOT begin local CPU pre-training (training happens on Kaggle GPU).
