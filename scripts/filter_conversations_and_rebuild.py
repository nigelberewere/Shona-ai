from pathlib import Path
import json
import re
import sys
import subprocess

def main():
    print("JOB: Filtering conversations and rebuilding clean corpus...")

    convo_path = Path("data/raw/conversations/shona_conversations.txt")
    if not convo_path.exists():
        print(f"[ERROR] Conversations file {convo_path} not found!")
        sys.exit(1)

    # 1. Load original conversations
    with open(convo_path, "r", encoding="utf-8") as f:
        original_lines = [l.strip() for l in f if l.strip()]

    print(f"Original conversations count: {len(original_lines)}")

    # 2. Define forbidden words (case-insensitive search)
    forbidden_words = [
        "Service", "IRA", "S&P", "Could you please", "Vimeo", 
        "Plastic", "translation", "Linaclotide", "bhizinesi", "makambani"
    ]
    forbidden_patterns = [w.lower() for w in forbidden_words]

    # 3. Filter lines
    filtered_lines = []
    removed_by_word = 0
    removed_by_len = 0

    for line in original_lines:
        line_lower = line.lower()
        # Check length
        if len(line) < 30:
            removed_by_len += 1
            continue
        # Check forbidden words
        has_forbidden = False
        for pat in forbidden_patterns:
            if pat in line_lower:
                has_forbidden = True
                break
        if has_forbidden:
            removed_by_word += 1
            continue
        filtered_lines.append(line)

    print(f"Filtered out {removed_by_len} lines because they are shorter than 30 characters.")
    print(f"Filtered out {removed_by_word} lines because they contain English/forbidden words.")
    print(f"Remaining conversations count: {len(filtered_lines)}")

    # 4. Save filtered conversations back to raw/conversations
    with open(convo_path, "w", encoding="utf-8") as f:
        for line in filtered_lines:
            f.write(line + "\n")
    print(f"Saved filtered conversations to {convo_path}")

    # 5. Load and update data/processed/all_clean.txt
    all_clean_path = Path("data/processed/all_clean.txt")
    if not all_clean_path.exists():
        print(f"[ERROR] Clean corpus {all_clean_path} not found!")
        sys.exit(1)

    with open(all_clean_path, "r", encoding="utf-8") as f:
        corpus_lines = [l.strip() for l in f if l.strip()]

    print(f"Current clean corpus line count: {len(corpus_lines)}")

    # Remove all lines matching original unfiltered conversations
    original_convo_set = set(original_lines)
    cleaned_corpus_lines = [l for l in corpus_lines if l not in original_convo_set]
    print(f"Corpus lines after removing unfiltered conversations: {len(cleaned_corpus_lines)}")

    # Add the filtered conversations (avoiding duplicates)
    corpus_set = set(cleaned_corpus_lines)
    added_convo = 0
    for line in filtered_lines:
        if line not in corpus_set:
            cleaned_corpus_lines.append(line)
            corpus_set.add(line)
            added_convo += 1

    print(f"Added {added_convo} filtered conversation lines to corpus.")
    print(f"New corpus total lines: {len(cleaned_corpus_lines)}")

    # Save corpus
    with open(all_clean_path, "w", encoding="utf-8") as f:
        for line in cleaned_corpus_lines:
            f.write(line + "\n")

    # 6. Regenerate splits 98/1/1
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

    # 7. Read final stats
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
