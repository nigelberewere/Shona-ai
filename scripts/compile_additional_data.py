import os
import re
import sys
import random
from pathlib import Path

# Large list of English stopwords to detect and remove English leakage
ENGLISH_STOPWORDS = {
    "the", "and", "of", "to", "a", "is", "that", "it", "in", "was", "for", "on", "are", 
    "as", "with", "his", "they", "i", "at", "be", "this", "have", "from", "or", "one", 
    "had", "by", "word", "but", "not", "what", "all", "were", "we", "when", "your", 
    "can", "said", "there", "use", "an", "each", "which", "she", "do", "how", "their", 
    "if", "will", "up", "other", "about", "out", "many", "then", "them", "these", "so", 
    "some", "her", "would", "make", "like", "him", "into", "has", "look", "two", "more", 
    "write", "go", "see", "number", "no", "way", "could", "people", "my", "than", "first", 
    "water", "been", "call", "who", "oil", "its", "now", "find", "long", "down", "day", 
    "did", "get", "come", "made", "may", "part", "such", "here", "there", "than", "then",
    "although", "because", "after", "before", "during", "through", "under", "over", "between"
}

def load_vocabulary():
    print("Loading Shona vocabulary whitelist...")
    words = set()
    
    # 1. Load shona_words.txt
    dict_path = "data/dictionaries/shona_words.txt"
    if os.path.exists(dict_path):
        with open(dict_path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w:
                    words.add(w)
        print(f"  Loaded {len(words)} unique Shona dictionary words.")
    
    # 2. Load all_clean.txt (current baseline)
    corpus_path = "data/processed/all_clean.txt"
    if os.path.exists(corpus_path):
        try:
            with open(corpus_path, "r", encoding="utf-8") as f:
                content = f.read().lower()
                corpus_words = set(re.findall(r'[a-z]+', content))
            words.update(corpus_words)
            print(f"  Loaded {len(corpus_words)} words from baseline corpus. Total whitelist: {len(words)}")
        except Exception as e:
            print(f"  WARNING: Failed to load words from corpus: {e}")
            
    return words

def clean_and_normalize_lines(raw_lines, shona_vocab, source_name="source"):
    clean_lines = []
    skipped_short = 0
    skipped_noise = 0
    skipped_english = 0
    skipped_non_shona = 0
    skipped_artifact = 0
    
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
            
        # Standard cleaning rules:
        # 1. Strip HTML/XML tags
        line = re.sub(r'<[^>]*>', '', line)
        # 2. Normalize whitespace
        line = re.sub(r'\s+', ' ', line).strip()
        
        # 3. Reject lines shorter than 20 chars
        if len(line) < 20:
            skipped_short += 1
            continue
            
        # 4. Reject morphological artifacts (chemunhu:)
        if "chemunhu:" in line:
            skipped_artifact += 1
            continue
            
        # 5. Reject lines where >50% of characters are non-alphabetic
        alpha_chars = sum(1 for c in line if c.isalpha())
        if alpha_chars / len(line) < 0.5:
            skipped_noise += 1
            continue
            
        # Tokenize lowercased words
        words = re.findall(r'[a-z]+', line.lower())
        if not words:
            skipped_noise += 1
            continue
            
        # 6. Reject English leakage:
        english_word_count = sum(1 for w in words if w in ENGLISH_STOPWORDS)
        if english_word_count > 1 or (english_word_count / len(words) > 0.08):
            skipped_english += 1
            continue
            
        # 7. Reject lines with very low Shona ratio
        absent_count = sum(1 for w in words if w not in shona_vocab)
        shona_ratio = 1.0 - (absent_count / len(words))
        if shona_ratio < 0.70:
            skipped_non_shona += 1
            continue
            
        clean_lines.append(line)
        
    unique_lines = list(dict.fromkeys(clean_lines))
    print(f"\n[{source_name.upper()}] Cleaning Summary:")
    print(f"  Raw lines processed:            {len(raw_lines):,}")
    print(f"  Skipped short lines (<20 ch):   {skipped_short:,}")
    print(f"  Skipped artifacts (chemunhu:):   {skipped_artifact:,}")
    print(f"  Skipped noise / non-alphabetic: {skipped_noise:,}")
    print(f"  Skipped English leakage:        {skipped_english:,}")
    print(f"  Skipped low Shona ratio:        {skipped_non_shona:,}")
    print(f"  Retained unique clean lines:    {len(unique_lines):,}")
    
    total_tokens = sum(len(l.split()) for l in unique_lines)
    print(f"  Total clean Shona tokens:       {total_tokens:,}")
    
    return unique_lines

def main():
    print("=== Compile and Integrate Additional Data Sprint ===")
    
    shona_vocab = load_vocabulary()
    
    # Paths to new sources
    masakhane_raw_path = "data/raw/masakhane/masakhane_shona.txt"
    literature_clean_path = "data/processed/literature/archive_org_clean.txt"
    voa_archive_raw_path = "data/raw/voa/voa_shona_archive.txt"
    
    new_source_lines = {}
    
    # 1. Clean Masakhane Shona news
    if os.path.exists(masakhane_raw_path):
        print(f"\nProcessing Masakhane dataset from {masakhane_raw_path}...")
        with open(masakhane_raw_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        new_source_lines["masakhane"] = clean_and_normalize_lines(lines, shona_vocab, "masakhane")
    else:
        print(f"\nWARNING: Masakhane raw file {masakhane_raw_path} not found!")
        
    # 2. Clean Internet Archive literature
    if os.path.exists(literature_clean_path):
        print(f"\nProcessing Internet Archive clean dataset from {literature_clean_path}...")
        # Since it was already cleaned in clean_archive_data.py, we just read it, but let's run a sanity check.
        with open(literature_clean_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        new_source_lines["literature"] = clean_and_normalize_lines(lines, shona_vocab, "literature")
    else:
        print(f"\nWARNING: Literature clean file {literature_clean_path} not found!")
        
    # 3. Clean VOA Shona Archive
    voa_lines = []
    if os.path.exists(voa_archive_raw_path):
        print(f"\nProcessing VOA Historical Archive 1 from {voa_archive_raw_path}...")
        with open(voa_archive_raw_path, "r", encoding="utf-8") as f:
            voa_lines.extend(f.readlines())
            
    voa_archive_raw_path_2 = "data/raw/voa/voa_shona_archive_2.txt"
    if os.path.exists(voa_archive_raw_path_2):
        print(f"Processing VOA Historical Archive 2 from {voa_archive_raw_path_2}...")
        with open(voa_archive_raw_path_2, "r", encoding="utf-8") as f:
            voa_lines.extend(f.readlines())
            
    if voa_lines:
        new_source_lines["voa_archive"] = clean_and_normalize_lines(voa_lines, shona_vocab, "voa_archive")
    else:
        print("\nWARNING: No VOA historical archive files found!")
        sys.exit(1)
        
    # Validation step: Show 5 samples for each successful source before adding
    print("\n" + "="*50)
    print("        QUALITY CHECK: 5 SAMPLE LINES PER SOURCE")
    print("="*50)
    
    for src, lines in new_source_lines.items():
        print(f"\n[{src.upper()}] Samples:")
        if lines:
            samples = random.sample(lines, min(5, len(lines)))
            for idx, s in enumerate(samples):
                try:
                    print(f"  {idx+1}. {s}")
                except Exception:
                    safe_s = s.encode('ascii', errors='replace').decode('ascii')
                    print(f"  {idx+1}. {safe_s}")
        else:
            print("  No clean lines available.")
            
    # Load original corpus
    baseline_corpus_path = "data/processed/all_clean.txt"
    if os.path.exists(baseline_corpus_path):
        with open(baseline_corpus_path, "r", encoding="utf-8") as f:
            baseline_lines = [l.strip() for l in f if l.strip()]
    else:
        print(f"ERROR: Baseline corpus file {baseline_corpus_path} not found!")
        sys.exit(1)
        
    baseline_tokens = sum(len(l.split()) for l in baseline_lines)
    print(f"\nBaseline Corpus Size: {len(baseline_lines):,} lines | {baseline_tokens:,} tokens")
    
    # Deduplicate new lines against baseline corpus to avoid duplicates
    baseline_set = set(baseline_lines)
    
    final_added_lines = []
    source_stats = {}
    
    for src, lines in new_source_lines.items():
        src_added = 0
        src_duplicate = 0
        for l in lines:
            if l not in baseline_set:
                final_added_lines.append(l)
                baseline_set.add(l)
                src_added += 1
            else:
                src_duplicate += 1
        source_stats[src] = {
            "added": src_added,
            "duplicate_with_baseline": src_duplicate,
            "tokens": sum(len(l.split()) for l in lines if l not in baseline_lines)
        }
        
    print("\nDeduplication Against Baseline:")
    for src, stat in source_stats.items():
        print(f"  {src.upper()}: Added {stat['added']:,} unique lines ({stat['tokens']:,} tokens), filtered {stat['duplicate_with_baseline']:,} baseline overlaps.")
        
    # Total new additions
    total_new_lines = len(final_added_lines)
    total_new_tokens = sum(len(l.split()) for l in final_added_lines)
    print(f"\nNet growth: +{total_new_lines:,} unique lines | +{total_new_tokens:,} unique Shona tokens")
    
    # Append to all_clean.txt
    new_corpus_lines = baseline_lines + final_added_lines
    
    # Deduplicate again just to be absolutely certain
    new_corpus_lines = list(dict.fromkeys(new_corpus_lines))
    new_corpus_tokens = sum(len(l.split()) for l in new_corpus_lines)
    print(f"Final Integrated Corpus Size: {len(new_corpus_lines):,} lines | {new_corpus_tokens:,} tokens")
    
    # Save the expanded corpus
    print(f"Saving final integrated corpus to {baseline_corpus_path}...")
    with open(baseline_corpus_path, "w", encoding="utf-8") as f:
        for line in new_corpus_lines:
            f.write(line + "\n")
            
    # Regenerate train/valid/test splits (98/1/1)
    print("\nRegenerating dataset splits (98/1/1)...")
    random.seed(42)
    random.shuffle(new_corpus_lines)
    
    n_total = len(new_corpus_lines)
    n_val = int(0.01 * n_total)
    n_test = int(0.01 * n_total)
    n_train = n_total - n_val - n_test
    
    train_lines = new_corpus_lines[:n_train]
    valid_lines = new_corpus_lines[n_train:n_train+n_val]
    test_lines = new_corpus_lines[n_train+n_val:]
    
    print(f"  Train: {len(train_lines):,} lines")
    print(f"  Valid: {len(valid_lines):,} lines")
    print(f"  Test:  {len(test_lines):,} lines")
    
    # Write splits
    with open("data/processed/train.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(train_lines) + "\n")
    with open("data/processed/valid.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(valid_lines) + "\n")
    with open("data/processed/test.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(test_lines) + "\n")
        
    # Write split stats to data/processed/stats.json
    import json
    stats = {
        "total_lines": n_total,
        "total_tokens": new_corpus_tokens,
        "train_lines": len(train_lines),
        "valid_lines": len(valid_lines),
        "test_lines": len(test_lines),
        "train_tokens": sum(len(l.split()) for l in train_lines),
        "valid_tokens": sum(len(l.split()) for l in valid_lines),
        "test_tokens": sum(len(l.split()) for l in test_lines),
    }
    with open("data/processed/stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
        
    print("\nIntegrated dataset splits successfully generated and saved!")
    
    # Write to a summary file for reporting
    with open("data/processed/sprint_report.json", "w", encoding="utf-8") as f:
        json.dump({
            "before": {
                "lines": len(baseline_lines),
                "tokens": baseline_tokens
            },
            "after": {
                "lines": n_total,
                "tokens": new_corpus_tokens
            },
            "net_additions": {
                "lines": total_new_lines,
                "tokens": total_new_tokens
            },
            "sources": source_stats
        }, f, indent=2)

if __name__ == "__main__":
    main()
