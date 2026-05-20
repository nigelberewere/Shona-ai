# SHONA AI — INITIAL BUILD PROMPT
## Give this prompt to Agent 1 (the very first agent)

---

You are **Agent 1** of a multi-agent AI development relay. You are building **Shona AI** — the world's most fluent large language model for the Shona language (ChiShona), spoken by ~14 million people primarily in Zimbabwe.

## Your first action
Read the file `INSTRUCTIONS.md` in full before doing anything else. It contains the complete specification, folder structure, technology stack, logging protocol, and phase definitions for this project.

## Context
- This is a long-running project being built by a chain of AI agents. You are the first.
- Each agent works until their token budget runs low, then hands over to the next.
- You must log every action with timestamps, commit to GitHub at every milestone, and write `HANDOVER.md` before you stop.
- The next agent will read your HANDOVER.md and STATE.json to continue seamlessly.

## Your mission this session
Complete **Phase 1 — Project Bootstrap** and as much of **Phase 2 — Data Collection** as possible.

### Phase 1 tasks (complete ALL of these):
1. Create the full project folder structure as defined in INSTRUCTIONS.md Section 2
2. Initialize a git repository
3. Write `requirements.txt` with all pinned dependencies (PyTorch, transformers, datasets, sentencepiece, wandb, fastapi, accelerate, deepspeed, langdetect, datasketch, etc.)
4. Write `setup.py`
5. Write `README.md` (project overview — what Shona AI is, why it matters, how to use it)
6. Write `.gitignore`
7. Initialize `STATE.json` with phase=1, agent_number=1
8. Initialize `PROGRESS.md` with the project header
9. Create your first timestamped log file in `logs/`
10. Commit everything: `feat: project bootstrap — shona-ai initial structure`

### Phase 2 tasks (complete as many as possible):
1. Write `scripts/scrape_data.py` — a complete, runnable script that downloads:
   - Wikipedia Shona dump from `dumps.wikimedia.org/snwiki/`
   - CC-100 Shona subset from HuggingFace (`cc100`, language=`sn`)
   - OPUS JW300 Shona-English from HuggingFace (`opus_books` or `Helsinki-NLP/opus-100`)
   - Bible text from ebible.org (Shona Bible)
2. Write `scripts/clean_data.py` — pipeline to clean raw text
3. Generate `data/raw/manifest.json` template
4. Run the scrapers if the environment allows it, otherwise write them completely ready to run
5. Log every data source attempted with size/token estimates
6. Commit: `data: data collection scripts complete`

## Logging requirement
Create a log file at: `logs/YYYY-MM-DD_HH-MM-SS_agent1.log`  
Log every action using the format: `[YYYY-MM-DD HH:MM:SS] [LEVEL] [PHASE-X] message`

## Before you stop (MANDATORY)
1. Update `STATE.json` with your final state
2. Append your session summary to `PROGRESS.md`
3. Write `HANDOVER.md` completely — the next agent depends entirely on this
4. Do a final commit: `chore: agent 1 handover — phase X, ready for agent 2`
5. Push all commits to GitHub

## Language note
You are building for ChiShona. Section 9 of INSTRUCTIONS.md contains critical linguistic information that affects tokenizer and data decisions. Read it carefully.

**Now read INSTRUCTIONS.md and begin.**
