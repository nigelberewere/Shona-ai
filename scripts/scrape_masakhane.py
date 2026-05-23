from datasets import load_dataset
import os
import re
from pathlib import Path

def download_masakhane():
    print("=== Downloading Masakhane Datasets ===")
    raw_dir = Path("data/raw/masakhane")
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path = raw_dir / "masakhane_shona.txt"
    
    shona_lines = []
    
    # 1. masakhane/masakhanews (sna)
    try:
        print("Loading masakhane/masakhanews (sna)...")
        for split in ["train", "validation", "test"]:
            ds = load_dataset("masakhane/masakhanews", "sna", split=split)
            print(f"  Loaded {split}: {len(ds)} rows.")
            for row in ds:
                # columns: 'headline', 'text'
                if row.get("headline"):
                    shona_lines.append(row["headline"].strip())
                if row.get("text"):
                    shona_lines.append(row["text"].strip())
    except Exception as e:
        print(f"WARNING: Failed to load masakhanews: {e}")
        
    # 2. masakhane/mafand (en-sna)
    try:
        print("Loading masakhane/mafand (en-sna)...")
        for split in ["validation", "test"]:
            ds = load_dataset("masakhane/mafand", "en-sna", split=split)
            print(f"  Loaded {split}: {len(ds)} rows.")
            for row in ds:
                # columns: 'translation' dict with 'en' and 'sna'
                trans = row.get("translation")
                if trans and trans.get("sna"):
                    shona_lines.append(trans["sna"].strip())
    except Exception as e:
        print(f"WARNING: Failed to load mafand: {e}")
        
    # 3. masakhane/afriqa (sna)
    try:
        print("Loading masakhane/afriqa (sna)...")
        for split in ["train", "validation", "test"]:
            # AfriQA splits might be named differently (e.g. dev, test)
            try:
                ds = load_dataset("masakhane/afriqa", "sna", split=split)
                print(f"  Loaded {split}: {len(ds)} rows.")
                for row in ds:
                    # columns: 'question', 'answers'
                    if row.get("question"):
                        shona_lines.append(row["question"].strip())
            except Exception as split_err:
                print(f"  Split {split} not found or failed: {split_err}")
    except Exception as e:
        print(f"WARNING: Failed to load afriqa: {e}")
        
    # Deduplicate and clean raw lines
    shona_lines = [l for l in shona_lines if l]
    unique_lines = list(dict.fromkeys(shona_lines))
    
    print(f"Extracted {len(unique_lines):,} unique raw Shona lines from Masakhane.")
    
    print(f"Writing to {out_path}...")
    with open(out_path, "w", encoding="utf-8") as f:
        for line in unique_lines:
            f.write(line + "\n")
            
    print("Masakhane data collection complete!")

if __name__ == "__main__":
    download_masakhane()
