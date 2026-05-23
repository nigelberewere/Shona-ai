import os
import re
from pathlib import Path

# Large list of English stopwords and common words that are extremely rare or non-existent in Shona.
ENGLISH_STOPWORDS = {
    "the", "and", "of", "to", "a", "is", "that", "it", "in", "was", "for", "on", "are", 
    "as", "with", "his", "they", "i", "at", "be", "this", "have", "from", "or", "one", 
    "had", "by", "word", "but", "not", "what", "all", "were", "we", "when", "your", 
    "can", "said", "there", "use", "an", "each", "which", "she", "do", "how", "their", 
    "if", "will", "up", "other", "about", "out", "many", "then", "them", "these", "so", 
    "some", "her", "would", "make", "like", "him", "into", "has", "look", "two", "more", 
    "write", "go", "see", "number", "no", "way", "could", "people", "my", "than", "first", 
    "water", "been", "call", "who", "oil", "its", "now", "find", "long", "down", "day", 
    "did", "get", "come", "made", "may", "part", "such", "here", "there", "than", "then",
    "although", "because", "after", "before", "during", "through", "under", "over", "between"
}

def load_dictionary():
    print("Loading Shona vocabulary...")
    words = set()
    
    # 1. Load shona_words.txt
    dict_path = "data/dictionaries/shona_words.txt"
    if os.path.exists(dict_path):
        with open(dict_path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w:
                    words.add(w)
        print(f"Loaded {len(words)} unique Shona dictionary words.")
    
    # 2. Load all_clean.txt
    corpus_path = "data/processed/all_clean.txt"
    if os.path.exists(corpus_path):
        try:
            with open(corpus_path, "r", encoding="utf-8") as f:
                content = f.read().lower()
                corpus_words = set(re.findall(r'[a-z]+', content))
            words.update(corpus_words)
            print(f"Loaded {len(corpus_words)} words from corpus. Total whitelist size: {len(words)}")
        except Exception as e:
            print(f"WARNING: Failed to load words from corpus: {e}")
            
    return words

def clean_archive_data():
    raw_path = "data/raw/literature/archive_org_shona.txt"
    out_dir = Path("data/processed/literature")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "archive_org_clean.txt"
    
    if not os.path.exists(raw_path):
        print(f"ERROR: Raw file {raw_path} not found.")
        return
        
    shona_vocab = load_dictionary()
    if not shona_vocab:
        print("ERROR: Shona vocabulary is empty.")
        return
        
    print(f"Processing and cleaning {raw_path}...")
    with open(raw_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    print(f"Total raw lines: {len(lines):,}")
    
    clean_lines = []
    skipped_short = 0
    skipped_non_shona = 0
    skipped_noise = 0
    skipped_english = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Strip XML/HTML tags
        line = re.sub(r'<[^>]*>', '', line)
        # Normalize whitespace
        line = re.sub(r'\s+', ' ', line).strip()
        
        # Rule 1: Length check (>= 20 characters)
        if len(line) < 20:
            skipped_short += 1
            continue
            
        # Rule 2: Alphabetic ratio check (>60% must be alphabetic)
        alpha_chars = sum(1 for c in line if c.isalpha())
        if alpha_chars / len(line) < 0.6:
            skipped_noise += 1
            continue
            
        # Extract lowercased alphabetic words
        words = re.findall(r'[a-z]+', line.lower())
        if not words:
            skipped_noise += 1
            continue
            
        # Rule 3: Detect English stopwords
        # If any word in the line is a common English stopword, increment count
        english_word_count = sum(1 for w in words if w in ENGLISH_STOPWORDS)
        # If more than 1 English stopword is found, or if English stopwords make up >10% of the line, reject!
        if english_word_count > 1 or (english_word_count / len(words) > 0.08):
            skipped_english += 1
            continue
            
        # Rule 4: Shona language ratio check (at least 75% of words must be in whitelist)
        absent_count = 0
        for w in words:
            if w not in shona_vocab:
                absent_count += 1
                
        shona_ratio = 1.0 - (absent_count / len(words))
        if shona_ratio < 0.75:
            skipped_non_shona += 1
            continue
            
        # Filter out lines that look like OCR noise / remnants with too many single letters
        single_letters = sum(1 for w in words if len(w) == 1 and w not in {'a', 'e', 'o', 'i', 'u'})
        if single_letters > 2 or (single_letters / len(words) > 0.15):
            skipped_noise += 1
            continue
            
        clean_lines.append(line)
        
    # Deduplicate
    unique_lines = list(dict.fromkeys(clean_lines))
    
    print("\nCleaning results:")
    print(f"  Skipped short lines (<20 chars): {skipped_short:,}")
    print(f"  Skipped noisy/non-alpha lines:  {skipped_noise:,}")
    print(f"  Skipped English sentences:      {skipped_english:,}")
    print(f"  Skipped non-Shona (low ratio):  {skipped_non_shona:,}")
    print(f"  Retained clean unique lines:    {len(unique_lines):,}")
    
    total_tokens = sum(len(l.split()) for l in unique_lines)
    print(f"  Total clean Shona tokens:       {total_tokens:,}")
    
    # Show 10 sample lines
    print("\nSample lines (10 random):")
    if unique_lines:
        import random
        samples = random.sample(unique_lines, min(10, len(unique_lines)))
        for s in samples:
            try:
                print(f"  - {s}")
            except Exception:
                # Fallback to ascii/safe representation to prevent terminal crashes
                safe_s = s.encode('ascii', errors='replace').decode('ascii')
                print(f"  - {safe_s}")
    else:
        print("  None!")
        
    print(f"\nWriting to {out_path}...")
    with open(out_path, "w", encoding="utf-8") as f:
        for line in unique_lines:
            f.write(line + "\n")
            
    print("Done!")

if __name__ == "__main__":
    clean_archive_data()
