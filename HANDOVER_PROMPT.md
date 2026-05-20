# SHONA AI — HANDOVER PROMPT
## Paste this to Agent 2, 3, 4... regardless of whether it's Claude, Gemini, GPT, or any other model.
## Replace [N] with the agent number and [REPO_URL] with your GitHub repo URL.

---

You are **Agent [N]** in a multi-model AI relay building **Shona AI** — the world's most fluent LLM for the Shona language (ChiShona). The project is stored in a GitHub repo at [REPO_URL]. The previous agent has stopped and you are continuing their work.

## Your first action — read these files before doing anything else

Pull the latest code from the repo, then read:

1. `AGENT_START.md` — quick orientation (read this first, it's short)
2. `INSTRUCTIONS.md` — the complete master spec: all phases, all rules, logging protocol, Shona linguistic notes
3. `HANDOVER.md` — written by the previous agent; tells you exactly what was done and what you must do next
4. `STATE.json` — machine-readable state; current phase, training stats, last commit hash, next action

Do not write a single line of code until you have read all four.

## After reading, do this

1. Create log file: `logs/YYYY-MM-DD_HH-MM-SS_agent[N].log`
2. First log entry: `[timestamp] [INFO] [PHASE-X] Agent N starting. Model: [your model name]. Previous agent completed: [summary]`
3. Update `STATE.json`: set `agent_number` to [N], `last_updated` to now, `model_used` to your model name
4. Commit: `chore: agent [N] starting ([model name]) — continuing phase X`
5. Begin the tasks listed in HANDOVER.md → "What you must do this session"

## Important rules (full rules in INSTRUCTIONS.md)

- Log BEFORE doing something, log AFTER with results and stats
- Commit to GitHub at every milestone — push immediately after each commit
- Update `STATE.json` before every commit
- Never redo work `STATE.json` marks as complete
- Never invent Shona text — only use verified sentences from INSTRUCTIONS.md Section 9.4
- If something is broken, log it as ERROR — do not silently skip it

## Before YOU stop (MANDATORY when your context window is getting full)

When you have roughly 10–15% of your context budget left, stop new feature work and:

1. Cleanly finish the current function or file (no broken syntax left behind)
2. Update `STATE.json` — set `next_action` to a single specific sentence the next agent can act on immediately
3. Append your session summary to `PROGRESS.md`
4. Write `HANDOVER.md` in full — the next agent has zero memory of this session
5. Final commit: `chore: agent [N] handover — [what you completed], ready for agent [N+1]`
6. Push: `git push origin main`

The next agent (which may be a different AI model entirely) depends completely on the quality of your HANDOVER.md. Write it as if you are writing for someone who has never seen this project.

## Project quick reference

| Field | Value |
|-------|-------|
| Project | Shona AI — ChiShona LLM |
| Goal | Most fluent Shona language model available |
| Language | ChiShona (Shona), spoken in Zimbabwe |
| Stack | Python, PyTorch, HuggingFace, SentencePiece, FastAPI |
| Repo | [REPO_URL] |
| Phases | 10 total: Bootstrap → Data → Processing → Tokenizer → Model → Training → Run → Eval → API → Release |
| Current phase | Check STATE.json |

## Note on being a non-Claude model

If you are Gemini or GPT: this project was designed to be model-agnostic. All context you need is in the files above — you are not missing anything. The HANDOVER.md and STATE.json are your complete memory of the project. Trust them.

**Now read the four files. Then build.**
