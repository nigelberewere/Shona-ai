import os
import random
import json

def merge_leipzig():
    base_path = "data/processed/all_clean.txt"
    leipzig_path = "data/processed/leipzig/leipzig_clean.txt"
    
    if not os.path.exists(base_path):
        print(f"ERROR: Base corpus {base_path} not found.")
        return
    if not os.path.exists(leipzig_path):
        print(f"ERROR: Leipzig cleaned corpus {leipzig_path} not found.")
        return
        
    print("Loading base corpus...")
    with open(base_path, "r", encoding="utf-8") as f:
        base_lines = [l.strip() for l in f if l.strip()]
        
    print("Loading Leipzig cleaned corpus...")
    with open(leipzig_path, "r", encoding="utf-8") as f:
        leipzig_lines = [l.strip() for l in f if l.strip()]
        
    print(f"Base corpus: {len(base_lines):,} lines, {sum(len(l.split()) for l in base_lines):,} tokens")
    print(f"Leipzig corpus: {len(leipzig_lines):,} lines, {sum(len(l.split()) for l in leipzig_lines):,} tokens")
    
    # Merge maintaining insertion order
    seen = {}
    for line in base_lines:
        seen[line] = True
        
    new_added = 0
    for line in leipzig_lines:
        if line not in seen:
            seen[line] = True
            new_added += 1
            
    merged_lines = list(seen.keys())
    merged_tokens = sum(len(l.split()) for l in merged_lines)
    
    print(f"\nMerge completed:")
    print(f"  New unique lines added from Leipzig: {new_added:,}")
    print(f"  Total lines in merged corpus:        {len(merged_lines):,}")
    print(f"  Total tokens in merged corpus:       {merged_tokens:,}")
    
    # Save back to all_clean.txt
    with open(base_path, "w", encoding="utf-8") as f:
        for line in merged_lines:
            f.write(line + "\n")
    print(f"Merged corpus saved to: {base_path}")
    
    # Regenerate splits 98/1/1
    print("\nRegenerating splits (98/1/1)...")
    random.seed(42)
    shuffled_lines = merged_lines.copy()
    random.shuffle(shuffled_lines)
    
    n_total = len(shuffled_lines)
    n_val = int(0.01 * n_total)
    n_test = int(0.01 * n_total)
    n_train = n_total - n_val - n_test
    
    train_lines = shuffled_lines[:n_train]
    valid_lines = shuffled_lines[n_train:n_train+n_val]
    test_lines = shuffled_lines[n_train+n_val:]
    
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
        "total_tokens": merged_tokens,
        "train_lines": len(train_lines),
        "valid_lines": len(valid_lines),
        "test_lines": len(test_lines),
        "train_tokens": sum(len(l.split()) for l in train_lines),
        "valid_tokens": sum(len(l.split()) for l in valid_lines),
        "test_tokens": sum(len(l.split()) for l in test_lines),
    }
    with open("data/processed/stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print("data/processed/stats.json updated.")
    
    # Update STATE.json
    state_path = "STATE.json"
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        state["data_stats"]["clean_tokens"] = merged_tokens
        if "leipzig_shona" not in state["data_stats"]["sources_complete"]:
            state["data_stats"]["sources_complete"].append("leipzig_shona")
        state["last_updated"] = "2026-05-24 07:45:00"
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        print("STATE.json updated.")
        
    # Draw and show 10 random sample lines
    print("\n10 Random Sample Lines from Cleaned and Merged Corpus:")
    samples = random.sample(merged_lines, min(10, len(merged_lines)))
    for idx, s in enumerate(samples):
        try:
            print(f"  {idx+1}. {s}")
        except Exception:
            safe_s = s.encode('ascii', errors='replace').decode('ascii')
            print(f"  {idx+1}. {safe_s}")

if __name__ == "__main__":
    merge_leipzig()
