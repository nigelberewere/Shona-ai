from opustools import OpusRead
import os
import re
from pathlib import Path

def check_shona_ratio(line, shona_dict):
    words = re.findall(r'[a-z]+', line.lower())
    if not words:
        return False
    absent = sum(1 for w in words if w not in shona_dict)
    return (absent / len(words)) <= 0.30

def main():
    print("Step 6 — Starting OPUS download and extraction...")
    
    # Ensure target directory exists
    raw_dir = Path("data/raw/opus")
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path = raw_dir / "opus_shona.txt"
    
    # Load dictionary
    dict_path = "data/dictionaries/shona_words.txt"
    shona_dict = set()
    if os.path.exists(dict_path):
        with open(dict_path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w:
                    shona_dict.add(w)
    print(f"Loaded {len(shona_dict)} dictionary words.")
    
    # List of corpora to process
    corpora = ["WikiMatrix", "OpenSubtitles", "Opus-100"]
    
    total_lines_saved = 0
    total_tokens_saved = 0
    
    with open(output_path, "w", encoding="utf-8") as out_file:
        for corpus in corpora:
            print(f"Processing OPUS corpus: {corpus}...")
            try:
                # We will write the aligned corpus to a temporary moses file
                temp_moses = f"temp_{corpus}.txt"
                
                # Run OpusRead to extract the aligned corpus
                # write='temp_{corpus}.txt' will create temp_{corpus}.txt.en and temp_{corpus}.txt.sn
                read = OpusRead(
                    directory=corpus,
                    source='en',
                    target='sn',
                    write_mode='moses',
                    write=temp_moses,
                    suppress_prompts=True
                )
                read.printPairs()
                
                sn_file = f"{temp_moses}.sn"
                en_file = f"{temp_moses}.en"
                
                # In case the language order is sn-en instead of en-sn
                if not os.path.exists(sn_file):
                    sn_file = f"{temp_moses}.en"
                    en_file = f"{temp_moses}.sn"
                    
                if os.path.exists(sn_file):
                    print(f"  Successfully extracted parallel files. Cleaning and filtering {sn_file}...")
                    corpus_lines = 0
                    with open(sn_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            # Clean HTML
                            line = re.sub(r'<[^>]*>', '', line)
                            # Normalize whitespace
                            line = re.sub(r'\s+', ' ', line).strip()
                            
                            if len(line) < 20:
                                continue
                            if not check_shona_ratio(line, shona_dict):
                                continue
                                
                            out_file.write(line + "\n")
                            corpus_lines += 1
                            total_lines_saved += 1
                            total_tokens_saved += len(line.split())
                    print(f"  Processed {corpus}: Saved {corpus_lines} high-quality Shona lines.")
                    
                    # Clean up temp files
                    if os.path.exists(sn_file): os.remove(sn_file)
                    if os.path.exists(en_file): os.remove(en_file)
                else:
                    print(f"  WARNING: Extracted Shona file {sn_file} not found!")
                    
            except Exception as e:
                print(f"  FAILED to process {corpus}: {e}")
                
    print("\n" + "="*50)
    print("            OPUS CORPUS SUMMARY")
    print("="*50)
    print(f"Total valid lines saved:      {total_lines_saved}")
    print(f"Total Shona tokens collected: ~{total_tokens_saved:,}")
    print(f"Output saved to:              {output_path}")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
