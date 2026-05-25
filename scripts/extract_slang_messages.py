import csv
import re
import sys
import random
import os

def main():
    if sys.platform.startswith("win"):
        sys.stdout.reconfigure(encoding='utf-8')
        
    SHONA_WORDS = {
        "ndiri", "ndinoda", "vanhu", "kuti", "uye", "zvino", "asi",
        "pane", "mwana", "amai", "baba", "mhoro", "zvakanaka", "munhu",
        "kubva", "kuenda", "vana", "chii", "here", "nhai", "shamwari",
        "hama", "musha", "nyika", "mangwanani", "masikati", "manheru",
        "maswera", "muswere", "makadii", "tiripo", "ndatenda", "maita",
        "chokwadi", "zvakanaka", "ndizvo", "ehe", "handiti", "saka",
        "nekuti", "kana", "zvimwe", "nguva", "mwari", "hona", "iwe",
        "isu", "imi", "iye", "vana", "tese", "mese", "vese", "chose",
        "zvose", "hapana", "pane", "ndipo", "ndiko", "ndiwo", "ndiyo",
        "makasimba", "muswere", "munyasha", "kwaziwai", "mhoroi",
        "hesi", "ndeipi", "kwakadii", "zvaita", "tatenda", "makorokoto"
    }

    SKIP_PHRASES = [
        "Media omitted", "media omitted", "Happy mothers", "Happy Mothers",
        "Good morning", "Sleep well", "Thank you", "Thank yu", "Thanx",
        "Good night", "Good evening", "Hi ", "Hie ", "Hello",
    ]

    def is_mostly_shona(text):
        words = text.lower().split()
        if len(words) < 2:
            return False
        shona_count = sum(1 for w in words if w in SHONA_WORDS)
        return shona_count / len(words) >= 0.2

    clean_messages = []
    repo_dir = "Working_with_shona-slang"

    for filename in [
        "shona_combined_dataset.csv",
        "slang_dataset_with_contexts_and_intent.csv"
    ]:
        file_path = os.path.join(repo_dir, filename)
        if not os.path.exists(file_path):
            print(f"[ERROR] {file_path} not found!")
            continue
            
        with open(file_path, encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                msg = row.get('message', '')
                if not msg:
                    continue
                msg = msg.strip()
                # Skip known English-only phrases
                if any(msg.startswith(p) for p in SKIP_PHRASES):
                    continue
                # Skip very short messages
                if len(msg) < 10:
                    continue
                # Skip messages that are all caps and short (spam/noise)
                if msg.isupper() and len(msg.split()) < 4:
                    continue
                # Keep if mostly Shona
                if is_mostly_shona(msg):
                    clean_messages.append(msg)

    # Deduplicate
    clean_messages = list(set(clean_messages))
    print(f"Clean Shona messages extracted: {len(clean_messages)}")
    
    # Save output
    os.makedirs("data/raw/social", exist_ok=True)
    out_path = "data/raw/social/whatsapp_shona.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(clean_messages))
    print(f"Saved clean messages to {out_path}")

    print("\n20 random samples:")
    random.seed(42)
    sample_msgs = random.sample(clean_messages, min(20, len(clean_messages)))
    for idx, msg in enumerate(sample_msgs):
        print(f"  {idx+1}: {msg}")

if __name__ == "__main__":
    main()
