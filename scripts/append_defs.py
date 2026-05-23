import json
from pathlib import Path

SRC = Path("shona dictionary/shona_dictionary_expanded.json")
ALL = Path("data/processed/all_clean.txt")

if not SRC.exists():
    print("MISSING_SRC")
    raise SystemExit(1)

data = json.load(open(SRC, "r", encoding="utf-8"))
defs = []
for entry in data:
    val = entry.get("definition_sn") or entry.get("definition")
    if val and isinstance(val, str):
        val = val.strip()
        if val:
            defs.append(val)

if not defs:
    print("NO_DEFS")
    raise SystemExit(0)

ALL.parent.mkdir(parents=True, exist_ok=True)
with open(ALL, "a", encoding="utf-8") as handle:
    for line in defs:
        handle.write(line + "\n")

print("APPENDED_DEFS", len(defs))
