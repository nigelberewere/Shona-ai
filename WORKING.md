# SHONA AI — WORKING STATE
## This file is updated by the agent BEFORE and AFTER every single task.
## It is the crash-recovery file. If an agent dies, this shows exactly what it was doing.

---

**Agent:** [N]  
**Model:** [model name]  
**Session started:** [YYYY-MM-DD HH:MM:SS]  
**Last updated:** [YYYY-MM-DD HH:MM:SS]  
**Phase:** [X]  

---

## Task queue for this session
> Agent fills this in AT THE START of the session, then checks off as it goes.
> If the agent dies, the next agent sees exactly what was done and what wasn't.

- [ ] Task 1 — [description]
- [ ] Task 2 — [description]
- [ ] Task 3 — [description]

---

## RIGHT NOW — what I am currently doing
> Agent updates this line BEFORE starting each task.
> This is the most important line in the file.
> If I die mid-task, the next agent knows exactly what was in progress.

```
CURRENT TASK: [exact description of what is being worked on right now]
FILE BEING WRITTEN: [path/to/file.py]
STARTED AT: [HH:MM:SS]
STATUS: [in progress / blocked / complete]
```

---

## Completed this session
> Agent appends here immediately after finishing each task. Never waits until the end.

| Time | Task | File | Commit hash |
|------|------|------|-------------|
| [HH:MM] | [task description] | [file path] | [hash] |

---

## If I was interrupted mid-task
> For the next agent — check the "RIGHT NOW" section above.
> The file listed there may be incomplete. Open it and check for:
> - Missing closing brackets/functions
> - TODO comments left mid-implementation  
> - Functions that raise NotImplementedError that should have been replaced

---

*This file is updated every single task. Last commit includes this file.*
