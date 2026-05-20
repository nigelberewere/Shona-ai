# Shona AI Project Guidelines

## Pre-Work Context Reading

Before writing any code or making changes:

1. **Read CLAUDE.md** — Understand the current technical context and any notes from previous sessions
2. **Read HANDOVER.md** — Learn what work was completed and what you must do next
3. **Read STATE.json** — Review the current build state, phase, and progress tracking

This ensures continuity and prevents duplicate or conflicting work.

## Logging and Audit Trail

Every action must be logged with timestamps to `logs/` for auditability and debugging:

- Create a timestamped log file when starting a new work session
- Log every major action: file modifications, commands run, decisions made, errors encountered
- Include timestamp and brief context for each entry
- Before finishing a session, ensure the log file is saved to `logs/`

Example:
```
[2026-05-20 12:15:00] Starting data preprocessing phase
[2026-05-20 12:15:45] Loaded training data: 10,000 samples
[2026-05-20 12:16:20] Applied tokenization to 8,500 samples
```

## Git Commits at Milestones

Commit to git at every completed milestone:

- After completing a phase (data prep, training, evaluation, etc.)
- After fixing significant bugs
- After adding new features or modules
- Use clear, descriptive commit messages
- Reference the phase name or feature in the commit message

Example:
```
git commit -m "Complete data preprocessing phase

- Loaded and tokenized 10K ChiShona samples
- Generated vocabulary of 25K unique tokens
- Split into train/val/test: 80/10/10"
```

## Key Project Files

- **INSTRUCTIONS.md** — Master spec with all phases and deliverables
- **ARCHITECTURE.md** — System design and component relationships
- **PROGRESS.md** — Detailed progress tracking per phase
- **DATA_SOURCES.md** — Data provenance and sourcing approach
- **EVALUATION.md** — Evaluation metrics and success criteria

Refer to these when unsure about scope, requirements, or success criteria.

## Before Asking for Help

- Check HANDOVER.md first—the answer may already be documented
- Review PROGRESS.md to understand what's been tried
- Look at relevant error logs in `logs/` for context

This reduces context-switching and ensures you're building on existing work.
