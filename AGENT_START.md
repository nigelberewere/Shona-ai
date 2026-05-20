# SHONA AI — AGENT START
## This file is read by every agent at the start of every session, regardless of which AI model you are.

---

## What you are doing

You are one agent in a relay chain building **Shona AI** — the most fluent large language model for the Shona language (ChiShona), spoken by ~14 million people in Zimbabwe. Agents before you have done work. You are picking up where they left off.

## Read these three files right now, in this order

```
1. INSTRUCTIONS.md   — the complete master spec (phases, rules, logging, Shona language notes)
2. HANDOVER.md       — written by the agent before you; tells you exactly what to do next
3. STATE.json        — machine-readable state; tells you which phase you are in
```

**Do not write any code until you have read all three.**

## After reading, your first actions are

1. Create a new log file: `logs/YYYY-MM-DD_HH-MM-SS_agentN.log`
2. Write your first log entry confirming you have read the files
3. Update `STATE.json` — increment `agent_number`, set `last_updated` to now
4. Make a start commit: `chore: agent N starting — phase X`

## Before you stop, you must

1. Finish the current file/function cleanly (no broken syntax)
2. Update `STATE.json` with `next_action` set to exactly what comes next
3. Append your session to `PROGRESS.md`
4. Write `HANDOVER.md` completely (format is in INSTRUCTIONS.md Section 8)
5. Final commit + push to GitHub

---

*Now read INSTRUCTIONS.md and begin.*
