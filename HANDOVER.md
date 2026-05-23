# HANDOVER — Agent 10 → Agent 11
**Date:** 2026-05-23
**Agent:** 10
**Model:** Human-supervised (Nigel + Claude)
**Reason for handover:** Phase 7 training is complete. Moving to Phase 8 evaluation.

## What was completed
- Data prep: corpus restored to 106,443 lines, 1,537,149 tokens
- Dictionary definitions (12,119 Shona definition_sn sentences) appended to corpus
- Phase 7 full training run completed on Kaggle T4 GPU
- 100,000 steps, final val_ppl = 94.1, final train_loss = 3.97
- Final checkpoint saved locally: training/checkpoints/shona_ai_final.pt (103.5MB)
- Checkpoint is NOT in git (gitignored) — it is on Nigel's local machine only
- HuggingFace upload deferred to Phase 10

## Current state
- **Phase:** 7 complete, 8 not started
- **Best checkpoint:** training/checkpoints/shona_ai_final.pt
- **val_ppl:** 94.1 at step 100,000
- **Tokenizer:** SentencePiece BPE, vocab=32000, fertility=1.154
- **Training data:** 104,314 train samples, 1,064 validation samples

## Training history summary
| Step | val_ppl |
|------|---------|
| 300 | 1,577 (pilot, CPU) |
| 1,000 | 428 |
| 5,000 | 275 |
| 10,000 | 215 |
| 50,000 | ~120 (estimated) |
| 100,000 | 94.1 |

## What you must do FIRST
Read AGENT_START.md and STATE.json. Confirm checkpoint exists at training/checkpoints/shona_ai_final.pt before doing anything else.

## What you must do this session (Phase 8)
1. Load the checkpoint and run sample generation — generate 5-10 Shona text samples from seed prompts and save to logs/phase8_samples.txt
2. Use verified Shona sentences from INSTRUCTIONS.md Section 9.4 as prompts only — never hallucinate Shona
3. Run evaluation metrics — perplexity on test.txt, character-level and word-level accuracy
4. Save all results to logs/phase8_eval.json
5. Update STATE.json: current_phase=8, phase_status.8=complete
6. Update PROGRESS.md with session note
7. Commit everything

## What NOT to do
- Do not upload to HuggingFace — that is Phase 10
- Do not start Phase 9 (inference API) until Phase 8 eval is committed
- Do not hallucinate Shona text — only use verified sentences from INSTRUCTIONS.md Section 9.4

## Known issues
- val_ppl of 94.1 means the model has learned Shona structure but will not be perfectly fluent
- Corpus was 1.5M tokens which is lean for a 25M parameter model — manage expectations on generation quality
- All pilot_checkpoints/ are INVALID (old causal shifting bug) — use only shona_ai_final.pt