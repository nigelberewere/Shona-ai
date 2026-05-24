# WORKING — Agent 15

**RIGHT NOW:** STOPPED — session ended. Leipzig data collection sprint complete, Gold baseline corpus successfully expanded to 3.51M clean tokens, splits regenerated, and STATE.json updated. Ready for GPU pre-training!

## Task queue for this session

- [x] Task 1: Initialize session files (log file, WORKING.md, HANDOVER.md, STATE.json) and commit.
- [x] Task 2: Audit OPUS API, SOAS Endangered Languages Archive, and LLOD catalogues for Shona data.
- [x] Task 3: Attempt direct downloads of JW300, GlobalVoices, and GNOME from CSC pouta storage and verify status.
- [x] Task 4: Discover active Shona corpora in Leipzig downloads.
- [x] Task 5: Download, extract, and strictly clean Leipzig 100K web corpus (sna-zw_web_2018_100K.tar.gz).
- [x] Task 6: Merge Leipzig clean sentences into all_clean.txt, run strict deduplication.
- [x] Task 7: Shuffled and regenerated dataset splits (98/1/1).
- [x] Task 8: Update stats.json, STATE.json, and progress files.
- [x] Task 9: Git commit and push all code and data to remote origin.

## Completed this session

| Time | Task | File | Commit hash |
|------|------|------|-------------|
| 07:32 | Task 1: Initialize session metadata | logs/2026-05-24_07-30-03_agent15.log | 5463dc6 |
| 07:45 | Task 2-4: Audited OPUS, SOAS, LLOD and Leipzig | scratch/list_opus_shona.py, test_leipzig_download.py | 720c853 |
| 07:53 | Task 5: Download & clean Leipzig 100K corpus | scripts/download_leipzig_corpora.py | 720c853 |
| 07:55 | Task 6-8: Merge, deduplicate, splits, state | scripts/merge_leipzig.py, STATE.json, stats.json | 995ade7 |
| 10:55 | Task 9: Handover & Documentation | HANDOVER.md, WORKING.md, PROGRESS.md | |
