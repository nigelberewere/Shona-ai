# HANDOVER — Agent [N] → Agent [N+1]

> **This file is rewritten by each agent before stopping.**  
> Previous handovers are preserved in `PROGRESS.md`. This file always reflects the CURRENT handover only.

---

**Date:** [YYYY-MM-DD HH:MM:SS]  
**From Agent:** [N]  
**To Agent:** [N+1]  
**Reason for handover:** [token budget / phase complete / other]  
**GitHub repo:** [https://github.com/your-org/shona-ai]  
**Last commit hash:** [abc1234]  

---

## What I completed this session

- [ ] *Replace with bullet list of everything you finished*
- [ ] Example: Completed `scripts/scrape_data.py` — downloads Wikipedia Shona + CC-100
- [ ] Example: Phase 2 data collection: 3/6 sources complete (4.2M raw tokens so far)

---

## Current build state

| Field | Value |
|-------|-------|
| Current phase | [X — Phase Name] |
| Phase status | [in_progress / complete] |
| Raw data collected | [X tokens from Y sources] |
| Clean data | [X tokens] |
| Training step | [N/A or step number] |
| Validation perplexity | [N/A or number] |
| Last passing quality gate | [Phase X] |

---

## What you must do FIRST (single most important action)

> *Be specific enough that the next agent can act on this in the first 30 seconds.*

Example: _"Run `python scripts/scrape_data.py --source bible` — the Wikipedia download is complete but the Bible scraper has not been run yet. The script is ready at `scripts/scrape_data.py`."_

[WRITE YOUR SPECIFIC FIRST ACTION HERE]

---

## What you must do this session (ordered priority list)

1. [Task 1 — include exact file paths, function names, commands to run]
2. [Task 2]
3. [Task 3]
4. [Continue to next phase: Phase X — task Y]

---

## Known issues / blockers

| Issue | Severity | Suggested fix |
|-------|----------|---------------|
| [describe issue] | [HIGH/MED/LOW] | [what to try] |

If none: `None known.`

---

## Files I created or modified this session

| File | Status | Notes |
|------|--------|-------|
| `scripts/scrape_data.py` | Created | Complete and tested |
| `data/raw/manifest.json` | Created | Template, needs populating as data comes in |
| `STATE.json` | Modified | Updated phase and stats |

---

## Commands to verify my work

```bash
# Verify folder structure
find . -type f | grep -v ".git" | sort

# Verify latest commit
git log --oneline -5

# Verify data stats
cat data/raw/manifest.json

# Run tests (if applicable)
python -m pytest tests/ -v
```

---

## Environment notes

- Python version: [3.x.x]
- Key packages installed: [list if non-standard installs were done]
- GPU available: [Yes/No — if yes, what]
- Any env vars needed: [e.g., WANDB_API_KEY, HF_TOKEN]
- Working directory: `/path/to/shona-ai`

---

## Do NOT do this

- [Pitfall 1 — e.g., "Do not re-download the Wikipedia dump, it's already at data/raw/wikipedia/"]
- [Pitfall 2 — e.g., "The ebible.org scraper requires a 30s delay between requests or gets rate-limited"]
- [Pitfall 3]

---

## Notes for the human operator

[Anything the human overseeing the project should know — costs incurred, decisions made, approvals needed, etc.]

---

*Written by Agent [N] | [timestamp] | Shona AI Project*
