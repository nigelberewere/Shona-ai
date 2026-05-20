# SHONA AI — MODEL-SPECIFIC NOTES
## Each agent should read the section for their model before starting work.

---

## Why this file exists

This project uses a relay of multiple AI models — Claude, Gemini, GPT, and potentially others. Each model has different strengths, context limits, and tool behaviors. This file tells each model how to work best within this project.

---

## For Claude (Claude Code in VS Code)

**Strengths for this project:** Long context, strong code generation, native file system access, git tool built-in.

**Context window:** 200K tokens — you can hold INSTRUCTIONS.md + HANDOVER.md + several code files in context at once.

**Tips:**
- Use the built-in git tool for all commits — do not shell out to bash for git
- `AGENT_START.md` will be auto-read if set as a project instruction
- You can read and write files natively — no need for shell scripts to move files
- Use `<function_calls>` style tool use for file operations
- Strong at PyTorch and HuggingFace code — trust your code generation here

**Watch out for:**
- Do not over-plan. You have strong reasoning but the mission is to BUILD.
- Token budget warning: you will be told when context is running out — write HANDOVER.md as soon as you see that warning, not after.

---

## For Gemini (Gemini 2.0/2.5 in VS Code or API)

**Strengths for this project:** Very long context (1M tokens), strong at reading large codebases, good Python.

**Context window:** Up to 1M tokens — you can potentially load the entire codebase at once.

**Tips:**
- Load all four orientation files at the start of your session explicitly
- Use your long context to read ALL existing code files before writing new ones — avoid duplication
- You are excellent at finding inconsistencies across many files — use this to audit previous agents' work
- For data processing tasks (Phase 2-3), you handle large text well — lean into this
- Shell out to bash for git operations: `git add -A && git commit -m "message" && git push`

**Watch out for:**
- Gemini can be verbose in explanations — this project rewards doing over explaining
- Keep log entries concise — one line per action, not paragraphs
- If you are in Gemini 1.5 or earlier, context limit is lower — be more selective about what you load
- Double-check all Shona text — do not generate unseen Shona. Use only Section 9.4 of INSTRUCTIONS.md.

---

## For GPT-4o / GPT-4 / o3 (via API, Copilot, or other interface)

**Strengths for this project:** Strong code quality, good at structured JSON output (STATE.json updates), reliable Python.

**Context window:** 128K tokens (GPT-4o) — you can hold INSTRUCTIONS.md + HANDOVER.md + current working files.

**Tips:**
- Prioritize reading STATE.json and HANDOVER.md first — you have less context than Claude/Gemini so be selective
- You are excellent at writing clean, well-structured Python — use this for the model architecture and training loop
- For STATE.json updates, generate the full JSON and write it atomically — avoid partial updates
- Shell out to bash for git: `git add -A && git commit -m "message" && git push`
- If using function calling / tools, map file read/write to those tools

**Watch out for:**
- 128K context fills faster than you think with long files — summarize INSTRUCTIONS.md mentally rather than re-reading fully each turn
- GPT models can be prone to "starting fresh" — aggressively check STATE.json to avoid redoing completed work
- Do not generate training data in Shona from scratch — only use verified sources (Section 9.4, INSTRUCTIONS.md)

---

## For any model — universal rules

Regardless of which model you are:

1. **STATE.json is truth.** If it says a phase is complete, it is complete. Do not redo it.
2. **HANDOVER.md is memory.** You have no memory of previous sessions. This file is all you have.
3. **Log everything.** Every model must write timestamped logs to `logs/`.
4. **Git commit at every milestone.** Every model. No exceptions.
5. **Do not generate Shona text beyond Section 9.4.** Hallucinated Shona poisons the project.
6. **Write HANDOVER.md before stopping.** The next model may be completely different from you.

---

## Model tracking in STATE.json

When you update STATE.json, include which model you are:

```json
{
  "agent_number": 3,
  "model_used": "gemini-2.0-flash",
  "model_provider": "google"
}
```

This helps the human operator and future agents understand who did what.

---

## Handover across different models — special note

When handing over FROM one model TO a different one, the outgoing agent should add a section to HANDOVER.md:

```markdown
## Note for incoming model
I am [Claude/Gemini/GPT]. The next agent may be a different model. Here is what you need to know:
- Files I created this session: [list]
- Code patterns I used: [e.g., "all training code uses HuggingFace Trainer API"]
- Anything model-specific I did that you should be aware of: [e.g., "I used Claude's file tool, not bash"]
```

---

*Model Notes v1.0 | Shona AI Project*
