from datasets import load_dataset
import os

def check_datasets():
    print("=== Testing HuggingFace datasets load ===")
    
    # 1. Helsinki-NLP/opus-100 en-sn
    try:
        print("Loading Helsinki-NLP/opus-100 en-sn...")
        ds = load_dataset("Helsinki-NLP/opus-100", "en-sn", split="train", timeout=15)
        print(f"SUCCESS: Loaded {len(ds)} train pairs.")
        print(f"Sample: {ds[0]}")
    except Exception as e:
        print(f"FAILED Helsinki-NLP/opus-100: {e}")
        
    # 2. castorini/afriberta_data
    try:
        print("Loading castorini/afriberta_data...")
        # Since afriberta_data is a large multi-lingual text corpus, it might require language codes.
        # Let's see if we can load it.
        ds = load_dataset("castorini/afriberta_data", trust_remote_code=True, split="train", timeout=15)
        print(f"SUCCESS: Loaded {len(ds)} train rows.")
        print(f"Sample: {ds[0]}")
    except Exception as e:
        print(f"FAILED castorini/afriberta_data: {e}")
        
    # 3. masakhane/mafand-mt en-sn
    try:
        print("Loading masakhane/mafand-mt en-sn...")
        ds = load_dataset("masakhane/mafand-mt", "en-sn", split="train", timeout=15)
        print(f"SUCCESS: Loaded {len(ds)} train pairs.")
        print(f"Sample: {ds[0]}")
    except Exception as e:
        print(f"FAILED masakhane/mafand-mt: {e}")

if __name__ == "__main__":
    check_datasets()
