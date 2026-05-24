from datasets import load_dataset
import os
import re

os.makedirs("data/raw/huggingface", exist_ok=True)

def light_clean(text):
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r'<[^>]+>', '', text)
    return text

def main():
    print("Attempting to load allenai/nllb with config 'eng_Latn-sna_Latn'...")
    try:
        ds = load_dataset("allenai/nllb", "eng_Latn-sna_Latn", trust_remote_code=True)
        shona_lines = [item['translation']['sna_Latn'] for item in ds['train']]
        
        cleaned_lines = []
        for line in shona_lines:
            cleaned = light_clean(line)
            if cleaned:
                cleaned_lines.append(cleaned)
                
        unique_lines = list(dict.fromkeys(cleaned_lines))
        
        print(f"NLLB Successfully loaded: {len(unique_lines)} unique Shona lines.")
        if unique_lines:
            print("--- 5 Sample lines from NLLB ---")
            for i in range(min(5, len(unique_lines))):
                print(f"  {i+1}: {unique_lines[i]}")
                
            out_file = "data/raw/huggingface/nllb_shona.txt"
            with open(out_file, "w", encoding="utf-8") as f:
                for line in unique_lines:
                    f.write(line + "\n")
            print(f"Saved {len(unique_lines)} lines to {out_file}")
            
    except Exception as e:
        print(f"NLLB failed: {e}")

if __name__ == "__main__":
    main()
