import random
import json
from datetime import datetime
from pathlib import Path

PROCESSED = Path("data/processed")
ALL = PROCESSED / "all_clean.txt"
STATS = PROCESSED / "stats.json"
TRAIN = PROCESSED / "train.txt"
VALID = PROCESSED / "valid.txt"
TEST = PROCESSED / "test.txt"

if not ALL.exists():
    print("MISSING_ALL")
    raise SystemExit(1)

with open(ALL, "r", encoding="utf-8") as handle:
    lines = [line.strip() for line in handle if line.strip()]

random.Random(42).shuffle(lines)
total = len(lines)
train_end = int(total * 0.98)
valid_end = int(total * 0.99)
train_lines = lines[:train_end]
valid_lines = lines[train_end:valid_end]
test_lines = lines[valid_end:]

PROCESSED.mkdir(parents=True, exist_ok=True)
with open(TRAIN, "w", encoding="utf-8") as h:
    for line in train_lines:
        h.write(line + "\n")
with open(VALID, "w", encoding="utf-8") as h:
    for line in valid_lines:
        h.write(line + "\n")
with open(TEST, "w", encoding="utf-8") as h:
    for line in test_lines:
        h.write(line + "\n")

clean_tokens = sum(len(line.split()) for line in lines)
stats = {
    "created_at": datetime.now().isoformat(),
    "sources": [],
    "combined": {"lines": len(lines), "tokens": clean_tokens},
    "splits": {"train": len(train_lines), "valid": len(valid_lines), "test": len(test_lines)},
}
with open(STATS, "w", encoding="utf-8") as h:
    json.dump(stats, h, indent=2, ensure_ascii=False)

print("SPLITS_WRITTEN", stats["combined"]["lines"], stats["combined"]["tokens"])
