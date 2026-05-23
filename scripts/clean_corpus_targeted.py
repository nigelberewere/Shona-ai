import os
import re
import random
import json
from pathlib import Path
from datetime import datetime

ENGLISH_STOPWORDS = set(w.lower() for w in [
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being", 
    "have", "has", "had", "do", "does", "did", "will", "would", "could", 
    "should", "may", "might", "shall", "can", "need", "dare", "ought", 
    "used", "and", "or", "but", "if", "in", "on", "at", "to", "for", 
    "of", "with", "by", "from", "up", "about", "into", "through", 
    "during", "before", "after", "above", "below", "between", "out", 
    "off", "over", "under", "again", "further", "then", "once", "here", 
    "there", "when", "where", "why", "how", "all", "both", "each", 
    "few", "more", "most", "other", "some", "such", "no", "not", 
    "only", "own", "same", "so", "than", "too", "very", "just", 
    "because", "as", "until", "while", "although", "Book", "Train", 
    "Europe", "Ready", "Connect", "Via", "USB", "Cotton", "Dress", "Current"
])

ADDITIONAL_ENGLISH_KEYWORDS = {"general", "name", "connect", "lizard", "laptops", "phones", "computer", "device", "screen", "web", "tickets", "plants", "garden", "e", "g", "ltd", "inc"}

def has_consecutive_english(line, limit=4):
    words = re.findall(r'[a-zA-Z]+', line.lower())
    consecutive = 0
    for w in words:
        if w in ENGLISH_STOPWORDS:
            consecutive += 1
            if consecutive >= limit:
                return True
        else:
            consecutive = 0
    return False

def has_english_in_parentheses(line):
    # Find anything inside parentheses
    matches = re.findall(r'\((.*?)\)', line)
    for content in matches:
        words = re.findall(r'[a-zA-Z]+', content.lower())
        for w in words:
            if w in ENGLISH_STOPWORDS or w in ADDITIONAL_ENGLISH_KEYWORDS:
                return True
    return False

def clean_corpus_targeted():
    all_clean_path = "data/processed/all_clean.txt"
    backup_path = "data/processed/all_clean.bak.txt"
    
    if not os.path.exists(all_clean_path):
        print(f"ERROR: file {all_clean_path} not found!")
        return
        
    with open(all_clean_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
        
    total_lines_before = len(lines)
    total_tokens_before = sum(len(line.split()) for line in lines)
    print(f"Total lines before targeted cleaning: {total_lines_before:,} (~{total_tokens_before:,} tokens)")
    
    cleaned_lines = []
    
    fails_url = 0
    fails_truncation = 0
    fails_price = 0
    fails_consec_english = 0
    fails_parentheses_english = 0
    
    for line in lines:
        # 1. Remove any line containing a URL
        if any(tok in line.lower() for tok in ["http", "www", ".com", ".net", ".org"]):
            fails_url += 1
            continue
            
        # 2. Remove any line ending with ...
        if line.endswith("..."):
            fails_truncation += 1
            continue
            
        # 3. Remove any line containing a price pattern — $ followed by digits
        if re.search(r'\$\d+', line):
            fails_price += 1
            continue
            
        # 4. Remove any line where more than 3 consecutive words are English (4 or more)
        if has_consecutive_english(line, limit=4):
            fails_consec_english += 1
            continue
            
        # 5. Remove lines containing text in parentheses that is English
        if has_english_in_parentheses(line):
            fails_parentheses_english += 1
            continue
            
        cleaned_lines.append(line)
        
    total_lines_after = len(cleaned_lines)
    total_tokens_after = sum(len(line.split()) for line in cleaned_lines)
    
    # Write to data/processed/all_clean.txt
    print(f"Writing targeted cleaned corpus to {all_clean_path}...")
    with open(all_clean_path, "w", encoding="utf-8") as f:
        for line in cleaned_lines:
            f.write(line + "\n")
            
    # Regenerate splits
    random.Random(42).shuffle(cleaned_lines)
    train_end = int(total_lines_after * 0.98)
    valid_end = int(total_lines_after * 0.99)
    
    train_lines = cleaned_lines[:train_end]
    valid_lines = cleaned_lines[train_end:valid_end]
    test_lines = cleaned_lines[valid_end:]
    
    splits_dir = Path("data/processed")
    with open(splits_dir / "train.txt", "w", encoding="utf-8") as f:
        for line in train_lines:
            f.write(line + "\n")
    with open(splits_dir / "valid.txt", "w", encoding="utf-8") as f:
        for line in valid_lines:
            f.write(line + "\n")
    with open(splits_dir / "test.txt", "w", encoding="utf-8") as f:
        for line in test_lines:
            f.write(line + "\n")
            
    # Write split statistics
    stats = {
        "created_at": datetime.now().isoformat(),
        "sources": [],
        "combined": {
            "lines": total_lines_after,
            "tokens": total_tokens_after
        },
        "splits": {
            "train": len(train_lines),
            "valid": len(valid_lines),
            "test": len(test_lines)
        }
    }
    with open(splits_dir / "stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
        
    print("\n" + "=" * 50)
    print("         TARGETED CLEANING PASS COMPLETE")
    print("=" * 50)
    print(f"Fails URL:                  {fails_url:,}")
    print(f"Fails truncation (...):     {fails_truncation:,}")
    print(f"Fails price pattern ($d):   {fails_price:,}")
    print(f"Fails consec English (>3):  {fails_consec_english:,}")
    print(f"Fails parenthesized English:{fails_parentheses_english:,}")
    print(f"Lines before vs after:   {total_lines_before:,} -> {total_lines_after:,}")
    print(f"Tokens before vs after:  {total_tokens_before:,} -> {total_tokens_after:,}")
    print("=" * 50 + "\n")
    
    if cleaned_lines:
        print("--- 10 Random Samples from Targeted Cleaned Corpus ---")
        random.seed(123)
        sample_indices = random.sample(range(total_lines_after), min(10, total_lines_after))
        for i, idx in enumerate(sample_indices):
            print(f"{i+1}: {cleaned_lines[idx]}")
    else:
        print("WARNING: Cleaned corpus is empty!")

if __name__ == "__main__":
    clean_corpus_targeted()
