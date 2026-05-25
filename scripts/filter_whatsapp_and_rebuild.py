from pathlib import Path
import json
import re
import sys
import subprocess

def main():
    print("JOB: Applying final filters to WhatsApp dataset and rebuilding corpus...")

    whatsapp_path = Path("data/raw/social/whatsapp_shona.txt")
    if not whatsapp_path.exists():
        print(f"[ERROR] WhatsApp file {whatsapp_path} not found!")
        sys.exit(1)

    # 1. Load extracted lines
    with open(whatsapp_path, "r", encoding="utf-8") as f:
        raw_lines = [l.strip() for l in f if l.strip()]

    print(f"Loaded {len(raw_lines)} raw WhatsApp lines.")

    # 2. Filter lines using skip words and len >= 10
    skip_words = ['kuricy', 'bhooooooo', 'pfeeeee', 'kkkkk', 'kkkk', 
                  'lol', 'omg', 'wtf', 'lmao', 'haha', 'hehe']
    
    clean_lines = []
    for line in raw_lines:
        if len(line) < 10:
            continue
        # Check if line contains any skip word (case-insensitive)
        has_skip = False
        line_lower = line.lower()
        for skip in skip_words:
            if skip in line_lower:
                has_skip = True
                break
        if not has_skip:
            clean_lines.append(line)

    print(f"After final filter: {len(clean_lines)} lines")

    # 3. Save filtered lines back to raw social folder
    with open(whatsapp_path, "w", encoding="utf-8") as f:
        for line in clean_lines:
            f.write(line + "\n")
    print(f"Saved filtered WhatsApp dataset to {whatsapp_path}")

    # 4. Load and update data/processed/all_clean.txt
    all_clean_path = Path("data/processed/all_clean.txt")
    if not all_clean_path.exists():
        print(f"[ERROR] Clean corpus {all_clean_path} not found!")
        sys.exit(1)

    with open(all_clean_path, "r", encoding="utf-8") as f:
        corpus_lines = [l.strip() for l in f if l.strip()]

    print(f"Current clean corpus line count: {len(corpus_lines)}")

    # Add the clean WhatsApp lines (making sure to avoid duplicates)
    corpus_set = set(corpus_lines)
    added_whatsapp = 0
    for line in clean_lines:
        if line not in corpus_set:
            corpus_lines.append(line)
            corpus_set.add(line)
            added_whatsapp += 1

    print(f"Added {added_whatsapp} new unique WhatsApp lines to clean corpus.")
    print(f"New corpus total lines (before final save): {len(corpus_lines)}")

    # Save deduplicated corpus
    with open(all_clean_path, "w", encoding="utf-8") as f:
        for line in corpus_lines:
            f.write(line + "\n")
    print(f"Saved updated clean corpus to {all_clean_path}")

    # 5. Regenerate splits 98/1/1
    print("Executing scripts/update_splits_stats.py to regenerate splits...")
    try:
        result = subprocess.run(
            [sys.executable, "scripts/update_splits_stats.py"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Splits script output:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error running update_splits_stats.py: {e}\n{e.stderr}")
        sys.exit(1)

    # 6. Read final stats
    stats_path = Path("data/processed/stats.json")
    if stats_path.exists():
        with open(stats_path, "r", encoding="utf-8") as f:
            stats = json.load(f)
        print("\n--- NEW CORPUS STATS ---")
        print(f"Total lines: {stats['combined']['lines']}")
        print(f"Total tokens (words): {stats['combined']['tokens']}")
        print(f"Train lines: {stats['splits']['train']}")
        print(f"Valid lines: {stats['splits']['valid']}")
        print(f"Test lines: {stats['splits']['test']}")
    else:
        print("[ERROR] stats.json was not generated!")

if __name__ == "__main__":
    main()
