import os
from datasets import load_dataset

# Ensure target directories exist
os.makedirs("data/raw/huggingface", exist_ok=True)

def light_clean(text):
    if not text:
        return ""
    text = text.strip()
    # Remove HTML tags if any
    import re
    text = re.sub(r'<[^>]+>', '', text)
    return text

def process_and_save(shona_lines, dataset_name):
    cleaned_lines = []
    for line in shona_lines:
        cleaned = light_clean(line)
        if cleaned:
            cleaned_lines.append(cleaned)
            
    # Deduplicate
    cleaned_lines = list(dict.fromkeys(cleaned_lines))
    
    if not cleaned_lines:
        print(f"[{dataset_name}] No valid lines found after cleaning.")
        return
        
    print(f"\nSuccessfully processed [{dataset_name}]: {len(cleaned_lines)} unique lines.")
    print(f"--- 5 Sample lines from {dataset_name} ---")
    for i in range(min(5, len(cleaned_lines))):
        print(f"  {i+1}: {cleaned_lines[i]}")
        
    out_file = f"data/raw/huggingface/{dataset_name}_shona.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        for line in cleaned_lines:
            f.write(line + "\n")
    print(f"Saved {len(cleaned_lines)} lines to {out_file}")

def main():
    print("JOB 3: Checking OPUS and HuggingFace datasets with trust_remote_code=True...")

    # Attempt 1 - OPUS Books
    try:
        print("Attempting to load opus_books (en-sn)...")
        ds = load_dataset("opus_books", "en-sn", trust_remote_code=True)
        shona_lines = [item['translation']['sn'] for item in ds['train']]
        process_and_save(shona_lines, "opus_books")
    except Exception as e:
        print(f"opus_books failed: {e}")

    # Attempt 2 - Helsinki NLP
    try:
        print("Attempting to load Helsinki-NLP/opus-100 (en-sn)...")
        ds = load_dataset("Helsinki-NLP/opus-100", "en-sn", trust_remote_code=True)
        shona_lines = [item['translation']['sn'] for item in ds['train']]
        process_and_save(shona_lines, "opus_100")
    except Exception as e:
        print(f"Helsinki failed: {e}")

    # Attempt 3 - FLORES evaluation set
    try:
        print("Attempting to load facebook/flores (sna_Latn)...")
        ds = load_dataset("facebook/flores", "sna_Latn", trust_remote_code=True)
        shona_lines = []
        if 'devtest' in ds:
            shona_lines.extend([item['sentence'] for item in ds['devtest']])
        if 'dev' in ds:
            shona_lines.extend([item['sentence'] for item in ds['dev']])
        process_and_save(shona_lines, "flores")
    except Exception as e:
        print(f"FLORES failed: {e}")

    # Attempt 4 - NLLB seed data
    try:
        print("Attempting to load allenai/nllb (sna_Latn-eng_Latn)...")
        ds = load_dataset("allenai/nllb", "sna_Latn-eng_Latn", trust_remote_code=True)
        shona_lines = [item['translation']['sna_Latn'] for item in ds['train']]
        process_and_save(shona_lines, "nllb")
    except Exception as e:
        print(f"NLLB failed: {e}")

    # Attempt 5 - CCMatrix
    try:
        print("Attempting to load yhavinga/ccmatrix (en-sn)...")
        ds = load_dataset("yhavinga/ccmatrix", "en-sn", trust_remote_code=True)
        shona_lines = [item['translation']['sn'] for item in ds['train']]
        process_and_save(shona_lines, "ccmatrix")
    except Exception as e:
        print(f"CCMatrix failed: {e}")

    # Attempt 6 - African news
    try:
        print("Attempting to load masakhane/masakhanews (sna)...")
        ds = load_dataset("masakhane/masakhanews", "sna", trust_remote_code=True)
        shona_lines = []
        for split in ds.keys():
            shona_lines.extend([item['text'] for item in ds[split]])
        process_and_save(shona_lines, "masakhanews")
    except Exception as e:
        print(f"masakhanews failed: {e}")

if __name__ == "__main__":
    main()
