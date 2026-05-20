# HANDOVER — Agent 2 → Agent 3
**Date:** 2026-05-20 12:41:00
**Agent:** 2
**Reason for handover:** Execution environment rate-limited; implemented code but could not run downloads here

## What I completed this session
- Implemented `scripts/scrape_data.py` — downloads Wikipedia (sn), CC-100 (sn), Shona Bible, and OPUS en-sn. Writes per-source .txt files to `data/raw/<source>/` and updates `data/raw/manifest.json` with token counts.
- Updated `STATE.json` to set `agent_number` to 2 and `current_phase` to 2; set `last_commit` to `feat: scrape_data.py implemented`.
- Created a timestamped agent log `logs/2026-05-20_12-41-00_agent2.log` recording actions and the execution-blocked error.
- Created a todo list tracking Phase 2 steps using the agent task manager.

## Current state
- **Phase:** 2 — Data Collection (in_progress)
- **Last commit (planned):** feat: scrape_data.py implemented
- **Last log entry:** [2026-05-20 12:41:05] Execution blocked: rate-limited by execution_subagent

## What you must do FIRST
Run the scraping script to perform downloads and generate real data files and manifest entries:

```bash
python scripts/scrape_data.py
```

Logs will be written to `logs/<YYYY-MM-DD_HH-MM-SS>_agent2.log`. After each source completes, commit with message:

```
data: <source> downloaded - Xk tokens
```

Also update `STATE.json` before each commit to record token counts and sources completed.

## What you must do this session (ordered)
1. Run `python scripts/scrape_data.py` and ensure each source finishes; commit after each source completes with the message format above.
2. Verify `data/raw/manifest.json` contains entries for each completed source with token counts.
3. Once all sources are downloaded, mark the todo `Run scripts/scrape_data.py to download sources` as completed and update `STATE.json` (`data_stats.raw_tokens`, `data_stats.sources_complete`).
4. Proceed to implement `scripts/clean_data.py` (language detection, normalization, deduplication) only after downloads are finished.

## Known issues / blockers
- Execution in this environment was rate-limited when attempting to run the scraping script via the automation tool. The script itself was written and saved; it must be run in an environment with network access (developer machine, CI runner, or cloud VM).

## Files I created or modified this session
- `scripts/scrape_data.py` — implemented download logic and manifest updates
- `STATE.json` — updated agent_number and current_phase and next_action
- `logs/2026-05-20_12-41-00_agent2.log` — session log

## Environment notes
- The scraping script uses `datasets` (HuggingFace), `requests`, and `xml.etree.ElementTree`. Ensure `requirements.txt` includes these packages and `git` is available for commits.
- Running the script will perform heavy downloads; prefer running on a machine with sufficient disk space and a stable network connection.

## Do NOT do this
- Do not implement `scripts/clean_data.py` until all raw sources finish downloading and the manifest is populated.
# HANDOVER — Agent [N] → Agent [N+1]

> **This file is rewritten by each agent before stopping.**  
> Previous handovers are preserved in `PROGRESS.md`. This file always reflects the CURRENT handover only.

---

**Date:** [YYYY-MM-DD HH:MM:SS]  
**From Agent:** [N]  
**Reason for handover:** Phase 2 scraping is now complete for the requested sources; next agent should start data cleaning
**Reason for handover:** [token budget / phase complete / other]  
**GitHub repo:** [https://github.com/your-org/shona-ai]  
- Implemented `scripts/scrape_data.py` with fallbacks:
	- Wikipedia Shona now falls back to the Wikimedia dump when the Hugging Face config is unavailable.
	- CC-100 Shona now falls back to `mc4/sn` when the CC-100 source URL is unavailable.
	- OPUS en-sn now falls back to the direct CCAligned zip archive and extracts aligned pairs.
- Ran the scraper successfully and produced raw source files for Wikipedia, CC-100 fallback text, Bible, and OPUS pairs.
- Updated `data/raw/manifest.json` with all completed sources and token counts.
- Updated `STATE.json` to reflect `raw_tokens = 5,193,376` and completed sources.
- Refreshed the session log files in `logs/` with the latest run output.
## What I completed this session

- **Last commit:** data: bible_shona downloaded - 585k tokens
- **Last log entry:** [2026-05-20 14:47:37] [MILESTONE] [PHASE-2] All scraping complete. Total tokens: ~5,193,376
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
1. Implement `scripts/clean_data.py`.
2. Run the cleaning pipeline and update `data/processed/` plus any stats manifest it creates.
3. Commit the cleaning work with the Phase 3 milestone message.

Example: _"Run `python scripts/scrape_data.py --source bible` — the Wikipedia download is complete but the Bible scraper has not been run yet. The script is ready at `scripts/scrape_data.py`."_
- CC-100 Shona is not available at the expected Statmt endpoint, so the pipeline currently uses `mc4/sn` as a fallback text source.
- The Wikipedia dataset config `20231101.sn` was unavailable in the installed dataset loader, so the pipeline falls back to the Wikimedia dump.
[WRITE YOUR SPECIFIC FIRST ACTION HERE]

- `STATE.json` — updated raw token totals and completed sources
- `logs/2026-05-20_14-45-28_agent2.log` — latest session log

1. [Task 1 — include exact file paths, function names, commands to run]
- `datasets==2.20.0` is currently installed in the environment, along with `pyarrow-hotfix`.
4. [Continue to next phase: Phase X — task Y]

- Do not revert the fallback behavior; it is required to keep the pipeline working in this environment.

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
