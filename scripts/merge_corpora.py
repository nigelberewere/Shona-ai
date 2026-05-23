import os
import shutil
from pathlib import Path

def merge():
    all_clean_path = Path("data/processed/all_clean.txt")
    backup_path = Path("data/processed/all_clean.bak.txt")
    
    voa_path = Path("data/raw/voa/voa_shona.txt")
    opus_path = Path("data/raw/opus/opus_shona.txt")
    
    if not all_clean_path.exists():
        print("ERROR: data/processed/all_clean.txt does not exist!")
        return
        
    print(f"Backing up all_clean.txt to {backup_path}...")
    shutil.copyfile(all_clean_path, backup_path)
    
    # Read existing clean lines
    with open(all_clean_path, "r", encoding="utf-8") as f:
        existing_lines = [line.strip() for line in f if line.strip()]
    existing_tokens = sum(len(line.split()) for line in existing_lines)
    print(f"Current all_clean.txt: {len(existing_lines):,} lines, {existing_tokens:,} tokens")
    
    # Read VOA lines
    voa_lines = []
    if voa_path.exists():
        with open(voa_path, "r", encoding="utf-8") as f:
            voa_lines = [line.strip() for line in f if line.strip()]
    voa_tokens = sum(len(line.split()) for line in voa_lines)
    print(f"VOA Shona to append: {len(voa_lines):,} lines, {voa_tokens:,} tokens")
    
    # Read OPUS lines
    opus_lines = []
    if opus_path.exists():
        with open(opus_path, "r", encoding="utf-8") as f:
            opus_lines = [line.strip() for line in f if line.strip()]
    opus_tokens = sum(len(line.split()) for line in opus_lines)
    print(f"OPUS Shona to append: {len(opus_lines):,} lines, {opus_tokens:,} tokens")
    
    # Merge them
    merged_lines = existing_lines + voa_lines + opus_lines
    merged_tokens = existing_tokens + voa_tokens + opus_tokens
    
    print(f"Writing merged corpus to {all_clean_path}...")
    with open(all_clean_path, "w", encoding="utf-8") as f:
        for line in merged_lines:
            f.write(line + "\n")
            
    print(f"SUCCESS: Merged corpus contains {len(merged_lines):,} lines, ~{merged_tokens:,} tokens.")

if __name__ == "__main__":
    merge()
