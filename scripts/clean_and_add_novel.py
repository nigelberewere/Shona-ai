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

def clean_novel_line(line):
    line = line.strip()
    if not line:
        return None
        
    # Check for chapter header patterns like "CHITSAUKO 1:" or "CHITSAUKO 1"
    line_lower = line.lower()
    if "chitsauko" in line_lower:
        if ":" in line:
            parts = line.split(":", 1)
            content = parts[1].strip()
            if len(content) < 15:
                return None
            line = content
        else:
            # e.g., "CHITSAUKO 1 Izwi romushakabvu"
            parts = re.split(r'chitsauko\s+\d+', line, flags=re.IGNORECASE)
            content = "".join(parts).strip()
            # Strip leading/trailing punctuation or whitespace that might be left
            content = re.sub(r'^[\s\:\-\.\,]+', '', content).strip()
            if len(content) < 15:
                return None
            line = content

    # Strip any page numbers or lines that are just numbers/digits
    if re.match(r'^\d+$', line):
        return None

    # Length filter
    if len(line) < 15:
        return None

    # Normalize whitespace
    line = re.sub(r'\s+', ' ', line).strip()
    return line

def main():
    safe_print("=== Processing Tambaoga Mwanangu Novel ===")
    
    novel_path = Path("data/raw/novels/Tambaoga Mwanangu.txt")
    if not novel_path.exists():
        safe_print(f"ERROR: Novel file {novel_path} does not exist.")
        return
        
    # Load and clean novel
    with open(novel_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()
        
    safe_print(f"Total raw lines in file: {len(raw_lines)}")
    
    cleaned_lines = []
    for rl in raw_lines:
        cl = clean_novel_line(rl)
        if cl:
            cleaned_lines.append(cl)
            
    # Remove duplicates from the novel itself while preserving order
    unique_cleaned_lines = list(dict.fromkeys(cleaned_lines))
    
    safe_print(f"Lines after light cleaning: {len(unique_cleaned_lines)}")
    
    # Show 5 random sample lines
    safe_print("\n5 random lines from the novel after cleaning:")
    samples = random.sample(unique_cleaned_lines, min(5, len(unique_cleaned_lines)))
    for idx, s in enumerate(samples):
        safe_print(f"  Sample {idx+1}: {s}")
        
    # Integrate into data/processed/all_clean.txt
    base_corpus_path = Path("data/processed/all_clean.txt")
    if not base_corpus_path.exists():
        safe_print(f"ERROR: Base corpus {base_corpus_path} not found.")
        return
        
    with open(base_corpus_path, "r", encoding="utf-8") as f:
        existing_lines = [l.strip() for l in f if l.strip()]
        
    before_lines = len(existing_lines)
    before_tokens = sum(len(l.split()) for l in existing_lines)
    safe_print(f"\nBefore integration: {before_lines:,} lines, {before_tokens:,} tokens.")
    
    # Merge and deduplicate
    seen_lines = {l: True for l in existing_lines}
    added_lines_count = 0
    novel_tokens = 0
    
    for line in unique_cleaned_lines:
        if line not in seen_lines:
            seen_lines[line] = True
            existing_lines.append(line)
            added_lines_count += 1
            novel_tokens += len(line.split())
            
    after_lines = len(existing_lines)
    after_tokens = sum(len(l.split()) for l in existing_lines)
    
    safe_print(f"Integration results:")
    safe_print(f"  Lines added from novel: {added_lines_count:,}")
    safe_print(f"  Approximate novel tokens added: {novel_tokens:,} words ({int(novel_tokens * 1.15):,} subword tokens)")
    safe_print(f"  After integration: {after_lines:,} lines, {after_tokens:,} tokens.")
    
    # Save back to data/processed/all_clean.txt
    with open(base_corpus_path, "w", encoding="utf-8") as f:
        for line in existing_lines:
            f.write(line + "\n")
    safe_print(f"Successfully saved merged corpus to {base_corpus_path}")
    
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
        if "tambaoga_mwanangu_novel" not in state["data_stats"]["sources_complete"]:
            state["data_stats"]["sources_complete"].append("tambaoga_mwanangu_novel")
        state["last_updated"] = "2026-05-24 14:38:00"
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        safe_print("STATE.json updated.")
        
    safe_print("\nNovel processing and integration complete!")

if __name__ == "__main__":
    main()
