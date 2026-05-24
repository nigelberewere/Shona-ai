from pathlib import Path
import json
import subprocess
import sys

def main():
    print("JOB 5: Appending new succeeded sources to all_clean.txt and regenerating splits...")

    all_clean_path = Path("data/processed/all_clean.txt")
    
    # 1. Read existing lines from all_clean.txt
    if all_clean_path.exists():
        with open(all_clean_path, "r", encoding="utf-8") as f:
            existing_lines = [line.strip() for line in f if line.strip()]
    else:
        existing_lines = []

    print(f"Existing clean corpus has {len(existing_lines)} lines.")
    existing_set = set(existing_lines)

    # 2. Define the new files to load
    new_files = [
        Path("data/raw/bible/shona_bible_v2.txt"),
        Path("data/raw/huggingface/masakhanews_shona.txt"),
        Path("data/raw/conversations/shona_conversations.txt")
    ]

    added_counts = {}
    for filepath in new_files:
        added_count = 0
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    cleaned = line.strip()
                    if cleaned and cleaned not in existing_set:
                        existing_lines.append(cleaned)
                        existing_set.add(cleaned)
                        added_count += 1
            added_counts[filepath.name] = added_count
            print(f"  Added {added_count} new lines from {filepath.name}.")
        else:
            print(f"  [WARNING] File {filepath.name} does not exist!")

    # 3. Write back to all_clean.txt
    print(f"Saving combined deduplicated corpus with {len(existing_lines)} lines to {all_clean_path}...")
    with open(all_clean_path, "w", encoding="utf-8") as f:
        for line in existing_lines:
            f.write(line + "\n")

    # 4. Regenerate splits 98/1/1 by executing scripts/update_splits_stats.py
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

    # 5. Read final stats
    stats_path = Path("data/processed/stats.json")
    if stats_path.exists():
        with open(stats_path, "r", encoding="utf-8") as f:
            stats = json.load(f)
        print("\n--- FINAL CORPUS STATS ---")
        print(f"Total lines: {stats['combined']['lines']}")
        print(f"Total tokens (words): {stats['combined']['tokens']}")
        print(f"Train lines: {stats['splits']['train']}")
        print(f"Valid lines: {stats['splits']['valid']}")
        print(f"Test lines: {stats['splits']['test']}")
    else:
        print("[ERROR] stats.json was not generated!")

if __name__ == "__main__":
    main()
