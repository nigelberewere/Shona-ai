# SHONA AI — MASTER INSTRUCTIONS
## Read this file completely before doing anything else. Re-read it whenever you feel uncertain.

---

## 1. MISSION STATEMENT

You are building **Shona AI** — the world's most fluent large language model for the Shona language (ChiShona), spoken primarily in Zimbabwe. The model must understand, generate, and reason in Shona at a level that surpasses every existing model on the market.

This is a multi-agent, iterative build. You are one agent in a relay chain. You will pick up exactly where the previous agent left off, do as much work as possible within your token budget, log everything, commit to GitHub, and leave a clean handover for the next agent.

**Your job is not to plan. Your job is to BUILD.**

---

## 2. PROJECT STRUCTURE

```
shona-ai/
├── INSTRUCTIONS.md          ← This file (always present in repo)
├── HANDOVER.md              ← Updated by every agent before stopping
├── PROGRESS.md              ← Append-only progress log
├── STATE.json               ← Machine-readable current build state
├── data/
│   ├── raw/                 ← Raw scraped/collected Shona text
│   ├── processed/           ← Cleaned, normalized text
│   ├── tokenized/           ← Tokenized datasets
│   └── eval/                ← Held-out evaluation sets
├── tokenizer/
│   ├── train_tokenizer.py
│   ├── tokenizer_config.json
│   └── vocab/
├── model/
│   ├── config.py            ← Model architecture config
│   ├── model.py             ← Core model definition
│   ├── attention.py         ← Attention mechanisms
│   └── embeddings.py
├── training/
│   ├── trainer.py           ← Main training loop
│   ├── dataset.py           ← Dataset loader
│   ├── optimizer.py         ← Optimizer + scheduler
│   ├── loss.py              ← Loss functions
│   └── config.yaml          ← Training hyperparameters
├── evaluation/
│   ├── eval.py              ← Evaluation harness
│   ├── benchmarks/          ← Shona-specific benchmarks
│   └── metrics.py           ← Perplexity, BLEU, custom metrics
├── inference/
│   ├── generate.py          ← Text generation
│   ├── api.py               ← FastAPI inference server
│   └── demo.py              ← CLI demo
├── scripts/
│   ├── scrape_data.py       ← Data collection scripts
│   ├── clean_data.py        ← Data cleaning pipeline
│   ├── prepare_dataset.py   ← Dataset preparation
│   └── upload_to_hub.py     ← HuggingFace Hub upload
├── tests/
│   ├── test_tokenizer.py
│   ├── test_model.py
│   └── test_data_pipeline.py
├── logs/
│   └── [YYYY-MM-DD_HH-MM-SS].log  ← Timestamped logs
├── requirements.txt
├── setup.py
├── .gitignore
└── README.md
```

---

## 3. TECHNOLOGY STACK

| Component | Choice | Reason |
|-----------|--------|--------|
| Base framework | PyTorch | Industry standard, flexible |
| Transformer library | HuggingFace Transformers | Tooling, hub, ecosystem |
| Base model for fine-tuning | `facebook/xglm-564M` or `bigscience/bloom-560m` | Multilingual base, African language exposure |
| Tokenizer | SentencePiece (BPE) | Handles Bantu morphology well |
| Data processing | datasets (HF) + pandas | Pipeline efficiency |
| Training acceleration | Accelerate + DeepSpeed (if GPU available) | Multi-GPU / mixed precision |
| Experiment tracking | Weights & Biases (wandb) | Logging, curves, comparison |
| Version control | Git + GitHub | All agents commit here |
| Inference server | FastAPI + uvicorn | Simple, fast API |
| Containerization | Docker | Reproducibility |

---

## 4. BUILD PHASES

Each phase has a completion condition. An agent must NOT move to the next phase until the current one is verified complete and committed.

### PHASE 1 — PROJECT BOOTSTRAP (Est. ~1 agent)
- [ ] Initialize git repo with full folder structure
- [ ] Write `requirements.txt` with all dependencies pinned
- [ ] Write `setup.py`
- [ ] Write `README.md` (project overview)
- [ ] Write `.gitignore`
- [ ] Initialize `STATE.json` with phase=1
- [ ] Write `PROGRESS.md` header
- [ ] First commit: `feat: project bootstrap`

### PHASE 2 — DATA COLLECTION (Est. ~2-3 agents)
Primary Shona text sources to target:
- [ ] **Bible (ChiShona Bible)** — Public domain, high quality, ~800K tokens
  - Source: `christos.gr/bible/` or `ebible.org`
- [ ] **Wikipedia Shona** — `sn.wikipedia.org` dump
  - Source: `dumps.wikimedia.org/snwiki/`
- [ ] **OPUS corpus** — parallel Shona-English data
  - Source: `opus.nlpl.eu` (JW300, CCAligned, WikiMatrix)
- [ ] **CommonCrawl Shona** — filtered web text
  - Source: `huggingface.co/datasets/cc100` (sn subset)
- [ ] **Shona news** — Herald Zimbabwe, NewsDay (scrape)
- [ ] **Shona books/literature** — Project Gutenberg equivalents
- [ ] **Custom scraped content** — Shona Facebook groups (public), forums
- [ ] Deduplicate all sources
- [ ] Generate `data/raw/manifest.json` (source, size, license, date)
- [ ] Commit: `data: raw collection complete - X tokens`

### PHASE 3 — DATA PROCESSING (Est. ~1-2 agents)
- [ ] Remove non-Shona text (language detection with `langdetect` + manual rules)
- [ ] Normalize Unicode (NFD → NFC)
- [ ] Normalize Shona-specific characters (handle diacritics: `ā`, `ē`, etc.)
- [ ] Remove HTML/XML artifacts
- [ ] Deduplicate at line and document level (MinHash LSH)
- [ ] Remove PII patterns (phone numbers, emails, IDs)
- [ ] Quality filter (perplexity-based filtering using a small n-gram LM)
- [ ] Split into train/valid/test (98/1/1)
- [ ] Write dataset stats to `data/processed/stats.json`
- [ ] Commit: `data: processing pipeline complete - X clean tokens`

### PHASE 4 — TOKENIZER TRAINING (Est. ~1 agent)
- [ ] Train SentencePiece BPE tokenizer on Shona corpus
- [ ] Vocabulary size: **32,000 tokens** (target ~95% fertility on Shona)
- [ ] Ensure coverage of: all Shona characters, common morphemes, tones
- [ ] Test tokenizer on sample sentences
- [ ] Measure fertility (tokens per word) — target < 1.8 for Shona
- [ ] Save tokenizer files to `tokenizer/`
- [ ] Write `tokenizer/README.md` with fertility stats
- [ ] Commit: `feat: shona sentencepiece tokenizer trained`

### PHASE 5 — MODEL ARCHITECTURE (Est. ~1 agent)
Build a decoder-only transformer. Config targets:

**Shona AI v0.1 (Small — for iteration speed)**
```
hidden_size: 512
num_layers: 8
num_heads: 8
intermediate_size: 2048
max_position_embeddings: 1024
vocab_size: 32000
parameters: ~25M
```

**Shona AI v1.0 (Base — production target)**
```
hidden_size: 768
num_layers: 12
num_heads: 12
intermediate_size: 3072
max_position_embeddings: 2048
vocab_size: 32000
parameters: ~117M
```

- [ ] Implement `model/config.py` (dataclass with all hyperparams)
- [ ] Implement `model/embeddings.py` (token + rotary position embeddings)
- [ ] Implement `model/attention.py` (multi-head causal attention + flash attention if available)
- [ ] Implement `model/model.py` (full GPT-style decoder stack)
- [ ] Write unit tests in `tests/test_model.py`
- [ ] Run forward pass sanity check (random weights, batch of 4)
- [ ] Commit: `feat: model architecture v0.1 implemented`

### PHASE 6 — TRAINING PIPELINE (Est. ~1-2 agents)
- [ ] Implement `training/dataset.py` (streaming dataset, dynamic batching)
- [ ] Implement `training/optimizer.py` (AdamW + cosine LR schedule + warmup)
- [ ] Implement `training/loss.py` (cross-entropy with label smoothing)
- [ ] Implement `training/trainer.py`:
  - Mixed precision (fp16/bf16)
  - Gradient clipping
  - Checkpoint saving every N steps
  - Eval every M steps
  - WandB logging
  - Resume from checkpoint
- [ ] Write `training/config.yaml` with all hyperparameters
- [ ] Run 100-step smoke test on small data slice
- [ ] Commit: `feat: training pipeline complete`

### PHASE 7 — TRAINING RUN (Est. ongoing agents)
- [ ] Launch training on full dataset
- [ ] Log every 50 steps to `logs/`
- [ ] Checkpoint every 1000 steps
- [ ] Commit checkpoints (or upload to HuggingFace Hub)
- [ ] Monitor for loss divergence — if loss doesn't decrease in 500 steps, flag in HANDOVER.md
- [ ] Target: perplexity < 15 on Shona validation set

### PHASE 8 — EVALUATION (Est. ~1 agent)
- [ ] Build Shona evaluation benchmarks:
  - **Shona-Bench-Gen**: 200 prompts, human-evaluated generation quality
  - **Shona-Bench-Cloze**: Fill-in-the-blank, 500 sentences
  - **Shona-Bench-NLI**: 300 natural language inference pairs
  - **Shona-Bench-Translation**: Shona↔English, 500 pairs (BLEU)
- [ ] Run full eval suite
- [ ] Compare against: GPT-4o (via API), XGLM-564M, mT5-base
- [ ] Write `evaluation/RESULTS.md`
- [ ] Commit: `eval: benchmark results for v0.1`

### PHASE 9 — INFERENCE & API (Est. ~1 agent)
- [ ] Implement `inference/generate.py` (greedy, top-k, top-p, temperature)
- [ ] Implement `inference/api.py` (FastAPI with `/generate`, `/health` endpoints)
- [ ] Write `Dockerfile`
- [ ] Write `docker-compose.yml`
- [ ] Write API documentation
- [ ] Commit: `feat: inference API complete`

### PHASE 10 — RELEASE (Est. ~1 agent)
- [ ] Upload model weights to HuggingFace Hub: `shona-ai/shona-ai-v1`
- [ ] Upload tokenizer to HuggingFace Hub
- [ ] Write model card (`README.md` on Hub)
- [ ] Write `CHANGELOG.md`
- [ ] Tag release: `v1.0.0`
- [ ] Commit: `release: shona-ai v1.0.0`

---

## 5. LOGGING PROTOCOL

Every agent MUST log every significant action. Log file naming:
```
logs/YYYY-MM-DD_HH-MM-SS_agentN.log
```

Log format (append only, never delete):
```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [PHASE-X] message
```

Log levels: `INFO`, `WARN`, `ERROR`, `MILESTONE`

Example:
```
[2024-01-15 09:23:11] [INFO] [PHASE-2] Starting Wikipedia Shona dump download
[2024-01-15 09:45:03] [MILESTONE] [PHASE-2] Wikipedia download complete: 2.3M tokens, 18,432 articles
[2024-01-15 09:45:04] [INFO] [PHASE-2] Beginning OPUS corpus download
[2024-01-15 10:12:33] [ERROR] [PHASE-2] OPUS JW300 download failed: HTTP 503. Retrying in 60s.
```

**Log at minimum:**
- Start of every script/function
- Completion of every script/function with stats
- Every file written (path + size)
- Every error (with full traceback)
- Every GitHub commit (hash)
- Token/step counts during training

---

## 6. GITHUB COMMIT PROTOCOL

Commit at every milestone — not just at the end. Use conventional commits:

```
feat:     New feature or file implemented
data:     Data collection or processing work
train:    Training-related work
eval:     Evaluation work
fix:      Bug fix
refactor: Code refactor
docs:     Documentation
chore:    Setup, config, dependencies
release:  Version releases
```

Commit message format:
```
<type>: <short description>

- Detail 1
- Detail 2
- Stats/numbers where relevant

Phase: X | Agent: N | Tokens remaining: ~X
```

**Push after every commit.** Do not batch commits.

---

## 7. STATE.json FORMAT

This file is the single source of truth for build state. Update it before every commit.

```json
{
  "project": "shona-ai",
  "version": "0.1.0",
  "last_updated": "YYYY-MM-DD HH:MM:SS",
  "agent_number": 1,
  "current_phase": 2,
  "phase_status": {
    "1": "complete",
    "2": "in_progress",
    "3": "not_started",
    "4": "not_started",
    "5": "not_started",
    "6": "not_started",
    "7": "not_started",
    "8": "not_started",
    "9": "not_started",
    "10": "not_started"
  },
  "data_stats": {
    "raw_tokens": 0,
    "clean_tokens": 0,
    "sources_complete": []
  },
  "training_stats": {
    "current_step": 0,
    "current_loss": null,
    "current_perplexity": null,
    "best_checkpoint": null
  },
  "last_commit": "",
  "last_commit_hash": "",
  "blocking_issues": [],
  "next_action": "Description of exactly what the next agent should do first"
}
```

---

## 8. HANDOVER.md FORMAT

Before an agent stops (due to token budget or task completion), it MUST write `HANDOVER.md` in full. This is the most important document for continuity.

```markdown
# HANDOVER — Agent [N] → Agent [N+1]
**Date:** YYYY-MM-DD HH:MM:SS  
**Agent:** N  
**Reason for handover:** [token budget / task complete]

## What I completed this session
- [Bullet list of everything finished]

## Current state
- **Phase:** X — [phase name]
- **Last commit:** [hash] — [message]
- **Last log entry:** [timestamp + message]

## What you must do FIRST
[Single most important next action, specific enough to act on immediately]

## What you must do this session (ordered)
1. [Task 1 — be specific, include file paths]
2. [Task 2]
3. ...

## Known issues / blockers
- [Issue and suggested resolution]

## Files I created or modified this session
- `path/to/file.py` — description
- `path/to/other.py` — description

## Environment notes
- [Python version, installed packages, any system dependencies]
- [GPU/CPU context if relevant]
- [Any env vars needed]

## Do NOT do this
- [Things to avoid, pitfalls I encountered]
```

---

## 9. SHONA LANGUAGE NOTES FOR AGENTS

Understanding Shona is critical for making correct technical decisions.

### 9.1 Language Family
- **Bantu language**, Niger-Congo family
- Spoken by ~14 million people, primarily Zimbabwe
- Main dialects: Karanga, Zezuru, Korekore, Manyika, Ndau (model should handle all)

### 9.2 Morphological Properties
- **Agglutinative**: words formed by combining morphemes
  - e.g., `ndinoda` = `ndi` (I) + `no` (present) + `da` (love) → "I love"
- **Noun class system**: 15 noun classes (like gender but more complex), each with agreement prefixes
  - Class 1: `mu-` (person) → `muntu` (person)
  - Class 2: `va-` (people) → `vanhu` (people)
  - Class 3: `mu-` (thing) → `muti` (tree/medicine)
- **Verb conjugation**: tense, aspect, subject, object all encoded in verb
- **Tone**: Shona is a tonal language (high/low tone) — important for tokenizer

### 9.3 Writing System
- Latin script (introduced by missionaries)
- Standard orthography set by the African Languages Research Institute (ALRI)
- Special characters rarely used in digital text — most Shona online text omits tonal marks
- Tokenizer must handle both tonal and non-tonal orthography

### 9.4 Common Evaluation Sentences
Use these to sanity-check model output at every phase:

| English | Shona |
|---------|-------|
| Hello, how are you? | Mhoro, makadii? |
| I am fine | Ndiri well / Ndiripo |
| What is your name? | Zita rako ndiani? |
| My name is John | Zita rangu ndiJohn |
| I love Zimbabwe | Ndinoda Zimbabwe |
| Water | Mvura |
| God | Mwari |
| Mother | Amai |
| Child | Mwana |
| We are going home | Tinoenda kumba |

### 9.5 Key Linguistic Challenges for the Model
1. **Code-switching**: Many Shona speakers mix Shona and English. Model should handle this.
2. **Dialectal variation**: `mabhero` (Karanga) vs `bhero` (Zezuru) — both correct
3. **Agglutination**: tokenizer must not over-segment morphemes
4. **Sparse data**: Shona is low-resource — every data point matters
5. **No standard punctuation norms**: data will be inconsistent

---

## 10. QUALITY GATES

Before marking any phase complete, the agent must pass these checks:

| Phase | Quality Gate |
|-------|-------------|
| 1 | All folders exist, all base files present, first commit pushed |
| 2 | `data/raw/manifest.json` exists, total raw tokens > 5M |
| 3 | Clean/raw ratio > 0.6, dedup ratio > 0.85, no empty files |
| 4 | Tokenizer fertility on Shona < 1.8 tokens/word |
| 5 | Forward pass runs without error on batch of 4 random inputs |
| 6 | 100-step smoke test loss decreases, no NaN |
| 7 | Validation perplexity < 15 |
| 8 | All 4 benchmarks run, results saved |
| 9 | API returns valid JSON on `/generate` with Shona prompt |
| 10 | Model card on HuggingFace, weights accessible |

---

## 11. AGENT RULES (NON-NEGOTIABLE)

1. **Read INSTRUCTIONS.md and HANDOVER.md before writing a single line of code.**
2. **Check STATE.json to know exactly where you are.**
3. **Never redo work that STATE.json marks as complete.**
4. **Log before you do, log after you do.**
5. **Commit before you stop — even if mid-phase.**
6. **Update STATE.json before every commit.**
7. **Write HANDOVER.md before running out of tokens.**
8. **If something is broken, log it as ERROR and document it in HANDOVER.md — do not silently skip.**
9. **Do not hallucinate Shona text. If you generate Shona for tests, use only the verified sentences in Section 9.4 or derive logically from grammar rules.**
10. **Prefer working code over perfect code. Ship, commit, document.**

---

## 12. EMERGENCY PROCEDURES

### If the previous agent left broken code:
1. Log the error with full traceback
2. Fix the immediate break
3. Note the fix in HANDOVER.md under "What I changed from previous agent"
4. Continue from there

### If data source URLs are dead:
1. Try the Wayback Machine (`web.archive.org`)
2. Check HuggingFace datasets for mirrors
3. Log fallback source used
4. Continue — do not block on a single source

### If training loss diverges (NaN or spikes):
1. Reduce learning rate by 10x
2. Check for data issues (empty batches, wrong dtype)
3. Reduce batch size
4. Log all changes
5. Restart from last valid checkpoint

### If GitHub push fails:
1. Save work locally
2. Log the error
3. Retry with `git push --force-with-lease`
4. If still failing, document the unpushed commits in HANDOVER.md

---

*This document is law. When in doubt, re-read it.*  
*Version: 1.0 | Project: Shona AI | Language: ChiShona*

---

## 13. RATE LIMIT & CRASH RECOVERY PROTOCOL

This section exists because agents can be cut off mid-task with no warning. The system below ensures the next agent can always recover cleanly.

### 13.1 The Three-Layer Safety System

**Layer 1 — Auto-commit watcher (human operator runs this)**  
Before starting ANY agent session, the human operator opens a separate terminal and runs:
```bash
bash scripts/watch_commit.sh /path/to/shona-ai
```
This commits ALL changes to GitHub every 5 minutes automatically. Even if the agent writes nothing to HANDOVER.md, the code files are safe.

**Layer 2 — WORKING.md (agent updates this constantly)**  
The agent must update `WORKING.md` before and after EVERY task. Not at the end of the session — after every single file written. This file always shows what the agent was doing at the moment it died.

**Layer 3 — Progressive HANDOVER.md (agent updates this as it goes)**  
The agent writes HANDOVER.md at the START of the session with the planned task list, then updates it as tasks complete. HANDOVER.md is never written only at the end.

### 13.2 Agent behavior — required changes

**At session start (first 5 actions):**
1. Read orientation files
2. Write `WORKING.md` with full task queue for this session
3. Set "RIGHT NOW" in WORKING.md to first task
4. Write initial HANDOVER.md with planned work
5. Commit: `chore: agent N started — working state initialized`

**Before starting each task:**
```
Update WORKING.md → "RIGHT NOW" section with current task name and file
```

**After completing each task:**
```
1. Check off task in WORKING.md task queue
2. Add row to WORKING.md "Completed this session" table
3. git add <completed file> && git commit -m "feat: <file> implemented"
4. Update STATE.json
5. Update HANDOVER.md "What I completed" section
```

**The order is non-negotiable:**  
`WORKING.md → write code → commit → WORKING.md → next task`

### 13.3 How the next agent recovers from a crashed session

If HANDOVER.md was not written (agent died early):

1. Read `WORKING.md` → "RIGHT NOW" tells you what was in progress
2. Read `WORKING.md` → task queue tells you what was planned
3. Check the file listed in "FILE BEING WRITTEN" — it may be incomplete
4. Run `git log --oneline -10` to see what was committed
5. Fix any incomplete file, then continue from the next unchecked task

### 13.4 Human operator checklist before every session

```
[ ] Terminal 1: cd shona-ai && bash scripts/watch_commit.sh .
[ ] Terminal 2: open agent session
[ ] Paste handover prompt to agent
[ ] Watch Terminal 1 — confirms commits every 5 mins
[ ] When agent stops: Ctrl+C in Terminal 1
```

### 13.5 Commit frequency rules

| Action | Commit? |
|--------|---------|
| Finish writing one complete file | YES — immediately |
| Finish one function inside a file | YES if function > 50 lines |
| Update STATE.json | YES — always commit with it |
| Update WORKING.md | YES — every update |
| Update HANDOVER.md | YES — every update |
| Write a log entry | No — log files committed by watcher |

**The rule: if you wrote something useful, commit it before moving on.**

