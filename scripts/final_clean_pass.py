import os
import random
import json

def final_clean_pass():
    corpus_path = "data/processed/all_clean.txt"
    if not os.path.exists(corpus_path):
        print(f"ERROR: Corpus path {corpus_path} not found.")
        return
        
    with open(corpus_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
        
    before_lines = len(lines)
    before_tokens = sum(len(l.split()) for l in lines)
    print(f"Before final cleaning: {before_lines:,} lines | {before_tokens:,} tokens")
    
    technical_words = {
        "helical", "compression", "torsion", "caffeine", "dmaa", "http", "usb",
        "blockchain", "bitcoin", "crypto", "pdf", "led", "lcd", "download",
        "upload", "software", "hardware", "database", "university", "college"
    }
    
    clean_lines = []
    skipped_wiki = 0
    skipped_technical = 0
    skipped_short = 0
    skipped_code = 0
    
    for line in lines:
        # Check Rule 1: Wiki markup & Code remnants
        # Purge single brackets, braces, pipes, XML tags, slashes, and code symbols
        if any(char in line for char in ['[', ']', '{', '}', '<', '>', '|', '\\', '/']):
            skipped_wiki += 1
            continue
            
        if line.startswith("*") or line.startswith("#"):
            skipped_wiki += 1
            continue
            
        # Reject programming operators
        if " = " in line or " ~= " in line or " == " in line or "local " in line or "function " in line:
            skipped_code += 1
            continue
            
        # Check Rule 2: Technical English terms mixed with Shona
        line_lower = line.lower()
        contains_tech = False
        for tech in technical_words:
            if tech in line_lower:
                contains_tech = True
                break
        if contains_tech:
            skipped_technical += 1
            continue
            
        # Check Rule 3: Lines shorter than 20 characters
        if len(line) < 20:
            skipped_short += 1
            continue
            
        clean_lines.append(line)
        
    # Deduplicate
    unique_lines = list(dict.fromkeys(clean_lines))
    
    after_lines = len(unique_lines)
    after_tokens = sum(len(l.split()) for l in unique_lines)
    
    print("\nFinal Cleaning Pass Summary:")
    print(f"  Skipped wiki markup & special characters: {skipped_wiki:,}")
    print(f"  Skipped code / programming syntax:        {skipped_code:,}")
    print(f"  Skipped technical noise lines:            {skipped_technical:,}")
    print(f"  Skipped short lines (<20 ch):             {skipped_short:,}")
    print(f"  Retained unique clean lines:              {after_lines:,} (diff: -{before_lines - after_lines:,})")
    print(f"  Total tokens after cleaning:              {after_tokens:,} (diff: -{before_tokens - after_tokens:,})")
    
    # Save back to all_clean.txt
    with open(corpus_path, "w", encoding="utf-8") as f:
        for line in unique_lines:
            f.write(line + "\n")
            
    # Regenerate splits 98/1/1
    print("\nRegenerating splits (98/1/1)...")
    random.seed(42)
    random.shuffle(unique_lines)
    
    n_total = len(unique_lines)
    n_val = int(0.01 * n_total)
    n_test = int(0.01 * n_total)
    n_train = n_total - n_val - n_test
    
    train_lines = unique_lines[:n_train]
    valid_lines = unique_lines[n_train:n_train+n_val]
    test_lines = unique_lines[n_train+n_val:]
    
    print(f"  Train split: {len(train_lines):,} lines")
    print(f"  Valid split: {len(valid_lines):,} lines")
    print(f"  Test split:  {len(test_lines):,} lines")
    
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
        
    print("\nSplits and statistics successfully saved.")
    
    # Draw and show 10 random sample lines
    print("\n10 Random Sample Lines from Cleaned Corpus:")
    samples = random.sample(unique_lines, min(10, len(unique_lines)))
    for idx, s in enumerate(samples):
        try:
            print(f"  {idx+1}. {s}")
        except Exception:
            safe_s = s.encode('ascii', errors='replace').decode('ascii')
            print(f"  {idx+1}. {safe_s}")

if __name__ == "__main__":
    final_clean_pass()
