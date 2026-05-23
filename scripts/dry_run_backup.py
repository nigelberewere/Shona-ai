import os
import re

def load_dictionary(path):
    words = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w:
                    words.add(w)
    return words

def check_backup():
    dict_path = "data/dictionaries/shona_words.txt"
    backup_path = "data/processed/all_clean.bak.txt"
    
    shona_words = load_dictionary(dict_path)
    
    with open(backup_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
        
    passes = 0
    total = len(lines)
    for line in lines:
        words = re.findall(r'[a-zA-Z]+', line.lower())
        if not words:
            continue
        absent = sum(1 for w in words if w not in shona_words)
        if (absent / len(words)) <= 0.25:
            passes += 1
            
    print(f"Backup lines passing: {passes:,} / {total:,} ({passes/total*100:.2f}%)")

if __name__ == "__main__":
    check_backup()
