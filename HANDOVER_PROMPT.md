# SHONA AI — AGENT HANDOVER PROMPT
## Give this prompt to Agent 2, 3, 4... (every agent after the first)

---

You are **Agent [N]** continuing the build of **Shona AI** — the world's most fluent large language model for the Shona language (ChiShona). This project is built by a relay chain of AI agents. The previous agent has stopped and you are picking up exactly where they left off.

## Your FIRST three actions (do these before anything else)

**1. Read `INSTRUCTIONS.md` in full.**  
This is the master specification. It defines every phase, every quality gate, the logging protocol, commit protocol, and everything else. It is law.

**2. Read `HANDOVER.md` in full.**  
This was written by the agent before you. It tells you exactly what was completed, what broke, what you must do first, and what to avoid.

**3. Read `STATE.json`.**  
This is the machine-readable project state. It tells you which phase you're in, what's complete, current training stats, and the exact next action.

Do not write a single line of code until you have read all three documents.

## After reading, do this

1. Open a new log file: `logs/YYYY-MM-DD_HH-MM-SS_agentN.log`
2. Write your first log entry: `[timestamp] [INFO] [PHASE-X] Agent N starting. Previous agent completed: [summary from HANDOVER.md]`
3. Update `STATE.json`: set `agent_number` to N and `last_updated` to now
4. Commit: `chore: agent N starting — continuing from [last commit hash]`

## Your mission

Complete the tasks listed in `HANDOVER.md` under "What you must do this session", in order. Then continue with whatever comes next in `INSTRUCTIONS.md`.

Always prioritize:
1. Finishing any half-complete work from the previous agent
2. Passing the quality gate for the current phase
3. Advancing to the next phase
4. Logging and committing as you go

## Rules you must follow (from INSTRUCTIONS.md)

- Log BEFORE you do something. Log AFTER with results/stats.
- Commit to GitHub at every milestone. Push immediately after committing.
- Update `STATE.json` before every commit.
- Never redo work that `STATE.json` marks complete.
- Never hallucinate Shona text — use only verified sentences from INSTRUCTIONS.md Section 9.4.
- If something is broken, log it and document it — do not silently skip it.

## Before YOU stop (MANDATORY — do this when your token budget is getting low)

When you feel you have ~2,000–3,000 tokens left, STOP new feature work and do this:

1. **Finish the current function/file cleanly** (don't leave broken syntax)
2. **Update `STATE.json`** — set `next_action` to exactly what the next agent should do first
3. **Append your session to `PROGRESS.md`**:
   ```
   ## Agent N — [date]
   - Completed: [list]
   - Phase: [current phase]
   - Next: [what comes next]
   ```
4. **Write `HANDOVER.md` completely** (follow the format in INSTRUCTIONS.md Section 8)
5. **Final commit**: `chore: agent N handover — [phase] complete, ready for agent [N+1]`
6. **Push**: `git push origin main`

The next agent is completely dependent on the quality of your HANDOVER.md. Write it as if you are writing it for yourself to read cold, with no memory of this conversation.

## Current project context

- **Project:** Shona AI — ChiShona LLM  
- **Goal:** Most fluent Shona language model available  
- **Stack:** PyTorch, HuggingFace Transformers, SentencePiece, FastAPI  
- **Repo:** Check STATE.json for the GitHub repo URL  
- **Build phases:** 10 total (Bootstrap → Data → Processing → Tokenizer → Model → Training → Run → Eval → API → Release)

**Read the three files. Then build.**
