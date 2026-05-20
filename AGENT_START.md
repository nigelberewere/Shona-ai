# SHONA AI — AGENT START
## Read this first. Every agent. Every session. Every model.

---

## What you are doing

You are one agent in a relay chain building **Shona AI** — the most fluent LLM for the Shona language (ChiShona), spoken by ~14 million people in Zimbabwe. You may be Claude, Gemini, GPT, or another model. It does not matter — the protocol is the same.

---

## Step 1 — Read these files before writing any code

```
1. INSTRUCTIONS.md    — master spec, all phases, all rules
2. HANDOVER.md        — what the previous agent did, what you do next
3. WORKING.md         — what the previous agent was doing when they stopped
4. STATE.json         — machine-readable phase and progress state
```

If HANDOVER.md is blank or a template → read WORKING.md first. It shows exactly where the previous agent died.

---

## Step 2 — Initialize your session (do all of these before any real work)

1. Create log file: `logs/YYYY-MM-DD_HH-MM-SS_agentN.log`
2. Write first log entry: `[timestamp] [INFO] [PHASE-X] Agent N starting. Model: [name].`
3. **Fill in WORKING.md completely** — write your full task queue for this session, set "RIGHT NOW" to your first task
4. **Update HANDOVER.md** — write it now with your planned work (you will update it as you go)
5. Update STATE.json: increment agent_number, set last_updated, set model_used
6. Commit everything: `chore: agent N started — working state initialized`

---

## Step 3 — Work loop (repeat for every task)

```
BEFORE each task:  update WORKING.md "RIGHT NOW" section
DO the task:       write the code / run the script
AFTER each task:   
  → git add <file> && git commit -m "feat: <file> done"
  → check off task in WORKING.md
  → add row to WORKING.md completed table
  → update HANDOVER.md "What I completed"
  → update STATE.json
```

**Commit after every single file. Not at the end of the session. After each file.**

---

## Step 4 — Before you stop

1. Set WORKING.md "RIGHT NOW" to: `STOPPED — session ended`
2. Update STATE.json with `next_action` set to one specific sentence
3. Write HANDOVER.md fully (format in INSTRUCTIONS.md Section 8)
4. Append session summary to PROGRESS.md
5. Final commit: `chore: agent N handover — [phase], ready for agent N+1`
6. Push: `git push origin main`

---

## The auto-commit watcher

The human operator should be running `scripts/watch_commit.sh` in a separate terminal. This commits your work every 5 minutes automatically. Even if you die mid-sentence, nothing is lost beyond 5 minutes.

---

*Read INSTRUCTIONS.md. Then build.*
