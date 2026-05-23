import os
import re
import random
import json
from pathlib import Path
from datetime import datetime

def rebuild():
    sources = {
        "voa": "data/raw/voa/voa_shona.txt",
        "opus_clean": "data/raw/opus/opus_shona_clean.txt",
        "bible": "data/raw/bible/shona_bible.txt",
        "wikipedia": "data/raw/wikipedia/shona_wiki.txt"
    }
    
    all_clean_path = "data/processed/all_clean.txt"
    
    raw_lines = []
    source_stats = {}
    
    for name, path in sources.items():
        if os.path.exists(path):
            print(f"Loading {name} lines from {path}...")
            with open(path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            raw_lines.extend(lines)
            source_stats[name] = {
                "raw_lines": len(lines),
                "raw_tokens": sum(len(line.split()) for line in lines)
            }
        else:
            print(f"WARNING: Source {name} file NOT found at {path}!")
            source_stats[name] = {"raw_lines": 0, "raw_tokens": 0}
            
    total_lines_before = len(raw_lines)
    total_tokens_before = sum(len(line.split()) for line in raw_lines)
    print(f"Total merged raw lines from gold sources before cleaning: {total_lines_before:,} (~{total_tokens_before:,} tokens)")
    
    cleaned_lines = []
    seen_lines = set()
    
    fails_pattern = 0
    fails_length = 0
    fails_non_alpha = 0
    fails_duplicate = 0
    
    for line in raw_lines:
        # 1. Strip </s> tags from all lines
        cleaned_line = line.replace("</s>", "").strip()
        cleaned_line = re.sub(r'\s+', ' ', cleaned_line).strip()
        
        # 4. Remove lines containing chemunhu:
        if "chemunhu:" in cleaned_line:
            fails_pattern += 1
            continue
            
        # 2. Remove lines shorter than 20 characters after stripping
        if len(cleaned_line) < 20:
            fails_length += 1
            continue
            
        # 3. Remove lines where more than 50% of characters are non-alphabetic
        alpha_count = sum(1 for c in cleaned_line if c.isalpha())
        if len(cleaned_line) > 0 and (alpha_count / len(cleaned_line)) < 0.50:
            fails_non_alpha += 1
            continue
            
        # 5. Remove exact duplicate lines
        line_key = cleaned_line.casefold()
        if line_key in seen_lines:
            fails_duplicate += 1
            continue
            
        seen_lines.add(line_key)
        cleaned_lines.append(cleaned_line)
        
    total_lines_after = len(cleaned_lines)
    total_tokens_after = sum(len(line.split()) for line in cleaned_lines)
    
    # Write to data/processed/all_clean.txt
    print(f"Writing rebuilt cleaned corpus to {all_clean_path}...")
    with open(all_clean_path, "w", encoding="utf-8") as f:
        for line in cleaned_lines:
            f.write(line + "\n")
            
    # Regenerate train/valid/test splits with 98/1/1 ratio
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
        "sources": source_stats,
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
    print("         REBUILD COMPLETE")
    print("=" * 50)
    print(f"Fails 'chemunhu:' pattern:    {fails_pattern:,}")
    print(f"Fails < 20 chars:             {fails_length:,}")
    print(f"Fails > 50% non-alpha chars:  {fails_non_alpha:,}")
    print(f"Fails duplicate check:        {fails_duplicate:,}")
    print(f"Lines before vs after:   {total_lines_before:,} -> {total_lines_after:,}")
    print(f"Tokens before vs after:  {total_tokens_before:,} -> {total_tokens_after:,}")
    print("=" * 50 + "\n")
    
    if cleaned_lines:
        print("--- 10 Random Samples from Rebuilt Corpus ---")
        random.seed(123)
        sample_indices = random.sample(range(total_lines_after), min(10, total_lines_after))
        for i, idx in enumerate(sample_indices):
            try:
                print(f"{i+1}: {cleaned_lines[idx]}")
            except UnicodeEncodeError:
                print(f"{i+1}: [UnicodeEncodeError: Line contains non-CP1252 characters]")
    else:
        print("WARNING: Cleaned corpus is empty!")

if __name__ == "__main__":
    rebuild()
