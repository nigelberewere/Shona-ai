import os
import re
import json
import random
from pathlib import Path

def safe_print(msg):
    try:
        print(msg)
    except Exception:
        try:
            print(msg.encode('ascii', errors='replace').decode('ascii'))
        except Exception:
            pass

# 100 common English words for strict stopword check
ENGLISH_STOPWORDS = {
    "the", "of", "and", "to", "a", "in", "is", "that", "it", "he", "was", "for", "on", 
    "are", "as", "with", "his", "they", "i", "at", "be", "this", "have", "from", "or", 
    "one", "had", "by", "word", "but", "not", "what", "all", "were", "we", "when", 
    "your", "can", "said", "there", "use", "an", "each", "which", "she", "do", "how", 
    "their", "if", "will", "up", "other", "about", "out", "many", "then", "them", 
    "these", "so", "some", "her", "would", "make", "like", "him", "into", "has", 
    "look", "two", "more", "write", "go", "see", "number", "no", "way", "could", 
    "people", "my", "than", "first", "been", "call", "who", "its", "now", "find"
}

SHONA_HINTS = {
    "kuti", "uye", "kana", "zvino", "pane", "muna", "ichi", "icho", "avo", "aya", 
    "ndiye", "nhasi", "asi", "saka", "baba", "mai", "vanhu", "munhu", "mwana", "nyika"
}

def clean_sentence(line):
    # Replace replacement characters if present
    line = line.replace("\ufffd", " ")
    
    # Strip any parenthesized/bracketed English explanations or details
    line = re.sub(r'\(.*?\)', '', line)
    line = re.sub(r'\[.*?\]', '', line)
    
    # Normalize whitespace
    line = re.sub(r'\s+', ' ', line).strip()
    
    # Strip leading list numbers/characters
    line = re.sub(r'^\d+(\.\d+)?[\.\)\s\-]+', '', line).strip()
    line = re.sub(r'^[a-zA-Z][\.\)\s\-]+', '', line).strip()
    
    return line

def is_mostly_english_or_numbers(line):
    words = re.findall(r'[a-zA-Z]+', line.lower())
    if not words:
        return True
        
    # Check English stopwords ratio
    english_word_count = sum(1 for w in words if w in ENGLISH_STOPWORDS)
    if len(words) > 0 and (english_word_count / len(words)) > 0.25:
        return True
        
    # Check for consecutive English words
    consecutive = 0
    for w in words:
        if w in ENGLISH_STOPWORDS:
            consecutive += 1
            if consecutive >= 3:
                return True
        else:
            consecutive = 0
            
    # Check non-alphabetic ratio
    non_alpha = sum(1 for c in line if not c.isalpha() and not c.isspace())
    if len(line) > 0 and (non_alpha / len(line)) > 0.40:
        return True
        
    return False

def clean_file(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
        
    cleaned_lines = []
    
    for line in lines:
        cleaned = clean_sentence(line)
        
        # Filter rules
        if len(cleaned) < 15:
            continue
            
        # Reject mostly numbers/English/garbled
        if is_mostly_english_or_numbers(cleaned):
            continue
            
        # Reject page headers/footers (single words or short lines that are just numbers/credits)
        if len(cleaned.split()) <= 2:
            # Check if any common Shona word is present, otherwise skip
            words = set(cleaned.lower().split())
            if not words.intersection(SHONA_HINTS):
                continue
                
        # Reject technical spam lines containing urls, emails, credits, etc.
        cleaned_lower = cleaned.lower()
        if any(tech in cleaned_lower for tech in ["http", "www", "whatsapp", "email", "phone", "tel:", "fax", "press"]):
            continue
            
        cleaned_lines.append(cleaned)
        
    # Deduplicate
    unique_cleaned = list(dict.fromkeys(cleaned_lines))
    return unique_cleaned

def main():
    safe_print("=== Step 4 — Cleaning and Filtering O-Level Study Materials ===")
    
    extracted_dir = Path("data/raw/SHONA/extracted")
    if not extracted_dir.exists():
        safe_print(f"ERROR: Extracted directory {extracted_dir} does not exist.")
        return
        
    files = list(extracted_dir.glob("*.txt"))
    safe_print(f"Found {len(files)} extracted files to clean.")
    
    cleaned_data_registry = {}
    
    for f_path in files:
        cleaned = clean_file(f_path)
        cleaned_data_registry[f_path.name] = cleaned
        
        safe_print(f"\nFile name: {f_path.name}")
        safe_print(f"Number of lines extracted after cleaning: {len(cleaned):,}")
        safe_print("5 sample lines after cleaning:")
        samples = random.sample(cleaned, min(5, len(cleaned)))
        for idx, s in enumerate(samples):
            safe_print(f"  Sample {idx+1}: {s}")
            
    # Step 5 — Add to corpus if quality is good
    safe_print("\n" + "="*60)
    safe_print("               CORPUS INTEGRATION (Step 5)")
    safe_print("="*60)
    
    base_corpus_path = Path("data/processed/all_clean.txt")
    if not base_corpus_path.exists():
        safe_print(f"ERROR: Base corpus {base_corpus_path} not found.")
        return
        
    # Load all existing clean lines
    with open(base_corpus_path, "r", encoding="utf-8") as f:
        existing_lines = [l.strip() for l in f if l.strip()]
    
    before_lines = len(existing_lines)
    before_tokens = sum(len(l.split()) for l in existing_lines)
    
    safe_print(f"Existing corpus size: {before_lines:,} lines, {before_tokens:,} tokens.")
    
    # Merge and deduplicate
    seen_lines = {l: True for l in existing_lines}
    new_added = 0
    total_added_tokens = 0
    
    for f_name, cleaned_lines in cleaned_data_registry.items():
        for line in cleaned_lines:
            if line not in seen_lines:
                seen_lines[line] = True
                existing_lines.append(line)
                new_added += 1
                total_added_tokens += len(line.split())
                
    after_lines = len(existing_lines)
    after_tokens = sum(len(l.split()) for l in existing_lines)
    
    safe_print(f"\nIntegration results:")
    safe_print(f"  New unique lines added from O-Level: {new_added:,}")
    safe_print(f"  New tokens added from O-Level:        {total_added_tokens:,}")
    safe_print(f"  Final corpus lines:                   {after_lines:,}")
    safe_print(f"  Final corpus tokens:                  {after_tokens:,}")
    
    # Save back to data/processed/all_clean.txt
    with open(base_corpus_path, "w", encoding="utf-8") as f:
        for line in existing_lines:
            f.write(line + "\n")
    safe_print(f"\nSuccessfully saved merged corpus to {base_corpus_path}")
    
    # Regenerate splits 98/1/1
    safe_print("\nRegenerating splits (98/1/1)...")
    random.seed(42)
    shuffled_lines = existing_lines.copy()
    random.shuffle(shuffled_lines)
    
    n_total = len(shuffled_lines)
    n_val = int(0.01 * n_total)
    n_test = int(0.01 * n_total)
    n_train = n_total - n_val - n_test
    
    train_lines = shuffled_lines[:n_train]
    valid_lines = shuffled_lines[n_train:n_train+n_val]
    test_lines = shuffled_lines[n_train+n_val:]
    
    safe_print(f"  Train split: {len(train_lines):,} lines")
    safe_print(f"  Valid split: {len(valid_lines):,} lines")
    safe_print(f"  Test split:  {len(test_lines):,} lines")
    
    with open("data/processed/train.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(train_lines) + "\n")
    with open("data/processed/valid.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(valid_lines) + "\n")
    with open("data/processed/test.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(test_lines) + "\n")
        
    # Update stats.json
    stats = {
        "total_lines": n_total,
        "total_tokens": after_tokens,
        "train_lines": len(train_lines),
        "valid_lines": len(valid_lines),
        "test_lines": len(test_lines),
        "train_tokens": sum(len(l.split()) for l in train_lines),
        "valid_tokens": sum(len(l.split()) for l in valid_lines),
        "test_tokens": sum(len(l.split()) for l in test_lines),
    }
    with open("data/processed/stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    safe_print("data/processed/stats.json updated.")
    
    # Update STATE.json
    state_path = "STATE.json"
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        state["data_stats"]["clean_tokens"] = after_tokens
        if "o_level_shona" not in state["data_stats"]["sources_complete"]:
            state["data_stats"]["sources_complete"].append("o_level_shona")
        state["last_updated"] = "2026-05-24 13:56:00"
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        safe_print("STATE.json updated.")
    
    safe_print("\nO-Level study materials sprint complete!")
    safe_print("="*60)

if __name__ == "__main__":
    main()
