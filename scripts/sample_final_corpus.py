import os
import random

def main():
    corpus_path = "data/processed/all_clean.txt"
    if not os.path.exists(corpus_path):
        print(f"ERROR: {corpus_path} not found.")
        return
        
    with open(corpus_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
        
    print(f"Total lines in final corpus: {len(lines):,}")
    
    # Sample 10 lines randomly
    random.seed(100) # fixed seed for reproducible check
    samples = random.sample(lines, 10)
    print("\n10 Random Sample Lines from Final Corpus:")
    for idx, s in enumerate(samples):
        try:
            print(f"  {idx+1}. {s}")
        except Exception:
            safe_s = s.encode('ascii', errors='replace').decode('ascii')
            print(f"  {idx+1}. {safe_s}")

if __name__ == "__main__":
    main()
