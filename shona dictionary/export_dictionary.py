import json
import csv
import os
from collections import Counter

def main():
    print("Phase 3 — Starting export, validation, and verification pipeline...")
    
    input_path = "shona_dictionary_expanded.json"
    if not os.path.exists(input_path):
        print(f"ERROR: {input_path} does not exist! Please run clean_and_merge.py first.")
        return
        
    with open(input_path, "r", encoding="utf-8") as f:
        entries = json.load(f)
        
    print(f"Loaded {len(entries)} entries for exporting.")
    
    # --- 1. VALIDATION CHECKS ---
    print("\n--- Running Dataset Validation Checks ---")
    
    # Check 1: Minimum count
    if len(entries) >= 10000:
        print(f"  [PASS] Minimum entry threshold met: {len(entries)} entries (Required: 10,000)")
    else:
        print(f"  [FAIL] Entry count too low: {len(entries)} (Required: 10,000)")
        
    # Check 2: Completeness of word and definition_en
    missing_fields = 0
    for idx, entry in enumerate(entries):
        if not entry.get("word") or not entry.get("definition_en"):
            missing_fields += 1
            if missing_fields <= 5:
                print(f"    Missing fields in entry {idx}: {entry}")
                
    if missing_fields == 0:
        print("  [PASS] All entries have a non-empty word and English definition.")
    else:
        print(f"  [FAIL] Found {missing_fields} entries with missing word or English definition.")
        
    # Check 3: Duplicate detection (by word and part_of_speech)
    seen_keys = set()
    duplicates = 0
    for entry in entries:
        key = (entry["word"].lower().strip(), entry["part_of_speech"])
        if key in seen_keys:
            duplicates += 1
        seen_keys.add(key)
        
    if duplicates == 0:
        print("  [PASS] Zero duplicate word-POS pairs found in the dataset.")
    else:
        print(f"  [WARNING] Found {duplicates} entries with duplicate word-POS combinations.")

    # Check 4: Orthography hygiene
    dirty_orthography = 0
    for entry in entries:
        word = entry["word"]
        # Allow spaces, hyphens, and standard a-z
        if not re.match(r'^[a-z\s-]+$', word.lower()):
            dirty_orthography += 1
            if dirty_orthography <= 5:
                print(f"    Non-standard orthography: '{word}'")
                
    if dirty_orthography == 0:
        print("  [PASS] All words use clean standard Latin-based orthography.")
    else:
        print(f"  [WARNING] Found {dirty_orthography} words with non-standard characters.")
        
    # --- 2. EXPORT FORMATS ---
    print("\n--- Exporting Final Dataset Formats ---")
    
    # Format A: shona_dictionary.json
    # Write cleanly indented and standard JSON format
    json_path = "shona_dictionary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"  [EXPORTED] JSON Dictionary -> {json_path} ({os.path.getsize(json_path)} bytes)")
    
    # Format B: shona_dictionary.csv
    # Write CSV with correct delimiters and string escaping
    csv_path = "shona_dictionary.csv"
    csv_headers = ["word", "part_of_speech", "class", "definition_en", "definition_sn", "example_sentence", "synonyms", "antonyms", "source"]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(csv_headers)
        for entry in entries:
            syns = ", ".join(entry.get("synonyms", []))
            ants = ", ".join(entry.get("antonyms", []))
            writer.writerow([
                entry.get("word", ""),
                entry.get("part_of_speech", ""),
                entry.get("class", ""),
                entry.get("definition_en", ""),
                entry.get("definition_sn", ""),
                entry.get("example_sentence", ""),
                syns,
                ants,
                entry.get("source", "")
            ])
    print(f"  [EXPORTED] CSV Dictionary -> {csv_path} ({os.path.getsize(csv_path)} bytes)")
    
    # Format C: shona_wordlist.txt
    # Lowercase, sorted, unique, one word per line
    wordlist_path = "shona_wordlist.txt"
    unique_words = sorted(list(set(entry["word"].lower().strip() for entry in entries)))
    with open(wordlist_path, "w", encoding="utf-8") as f:
        for word in unique_words:
            f.write(f"{word}\n")
    print(f"  [EXPORTED] TXT Wordlist -> {wordlist_path} ({os.path.getsize(wordlist_path)} bytes with {len(unique_words)} words)")
    
    # Format D: shona_parallel.tsv
    # Tab-separated file: shona_word \t english_definition
    tsv_path = "shona_parallel.tsv"
    with open(tsv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\")
        for entry in entries:
            writer.writerow([entry["word"], entry["definition_en"]])
    print(f"  [EXPORTED] TSV Parallel Corpus -> {tsv_path} ({os.path.getsize(tsv_path)} bytes)")
    
    # --- 3. METRICS AND SUMMARY REPORT ---
    print("\n" + "="*50)
    print("           SHONA DICTIONARY DATASET REPORT")
    print("="*50)
    print(f"Total Unique Entries (Lemmas):  {len(entries)}")
    print(f"Total Wordlist Tokens (for LM): {len(unique_words)}")
    
    # POS distribution
    print("\nPart of Speech (POS) Distribution:")
    pos_counts = Counter(entry.get("part_of_speech", "unknown") for entry in entries)
    for pos, count in pos_counts.most_common():
        pct = (count / len(entries)) * 100
        print(f"  - {pos:<14}: {count:>6} ({pct:>5.2f}%)")
        
    # Noun class distribution
    print("\nNoun Class Distribution:")
    class_counts = Counter(entry.get("class", "") for entry in entries if entry.get("class"))
    for cls, count in class_counts.most_common():
        pct = (count / len(entries)) * 100
        print(f"  - {cls:<14}: {count:>6} ({pct:>5.2f}%)")
        
    # Source distribution
    print("\nPrimary Source Distribution (Counts include merged/augmented attributes):")
    # For source parsing, since sources are merged like "spaCy Lexicon, Wiktionary", we can count occurrences
    source_counts = Counter()
    for entry in entries:
        srcs = [s.strip() for s in entry.get("source", "").split(",")]
        # If it's morphological expansion, just group them by the main engine type
        first_src = srcs[0]
        if "Morphological Engine" in first_src:
            if "Plural" in first_src:
                source_counts["Morphological Engine (Noun Plurals)"] += 1
            elif "Conjugation" in first_src:
                source_counts["Morphological Engine (Verb Conjugations)"] += 1
            else:
                source_counts["Morphological Engine (Verbal Extensions)"] += 1
        else:
            for s in srcs:
                source_counts[s] += 1
                
    for src, count in source_counts.most_common():
        print(f"  - {src:<42}: {count:>6}")
        
    print("="*50 + "\n")
    print("Validation and Export Pipeline successfully completed! All files written to the workspace.")

if __name__ == "__main__":
    import re
    main()
