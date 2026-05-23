import urllib.request
import zipfile
import io
import os
import re
from pathlib import Path

def load_dictionary(dict_path):
    """
    Loads valid Shona words from a dictionary file and our existing corpus into a set.
    """
    print(f"Loading Shona dictionary from {dict_path}...")
    words = set()
    if os.path.exists(dict_path):
        with open(dict_path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w:
                    words.add(w)
        print(f"Loaded {len(words)} unique Shona dictionary words.")
    else:
        print(f"WARNING: Dictionary file {dict_path} not found!")
        
    # Super vocabulary enhancement using all_clean.txt corpus
    corpus_path = "data/processed/all_clean.txt"
    if os.path.exists(corpus_path):
        print(f"Loading Shona words from corpus {corpus_path}...")
        try:
            with open(corpus_path, "r", encoding="utf-8") as f:
                content = f.read().lower()
                corpus_words = set(re.findall(r'[a-z]+', content))
            words.update(corpus_words)
            print(f"Loaded {len(corpus_words)} words from corpus. Total vocabulary size: {len(words)}")
        except Exception as e:
            print(f"WARNING: Failed to load words from corpus: {e}")
            
    return words

def check_shona_ratio(line, shona_dict):
    words = re.findall(r'[a-z]+', line.lower())
    if not words:
        return False
    absent = sum(1 for w in words if w not in shona_dict)
    return (absent / len(words)) <= 0.30

def clean_and_process_sn_file(file_content_bytes, out_file, shona_dict):
    lines_saved = 0
    tokens_saved = 0
    text_content = file_content_bytes.decode("utf-8", errors="ignore")
    
    for line in text_content.splitlines():
        line = line.strip()
        # Clean HTML tags
        line = re.sub(r'<[^>]*>', '', line)
        # Normalize whitespace
        line = re.sub(r'\s+', ' ', line).strip()
        
        if len(line) < 20:
            continue
        if not check_shona_ratio(line, shona_dict):
            continue
            
        out_file.write(line + "\n")
        lines_saved += 1
        tokens_saved += len(line.split())
        
    return lines_saved, tokens_saved

def download_and_extract_corpus(url, out_file, shona_dict):
    print(f"Downloading corpus from: {url}...")
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    
    try:
        import ssl
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=context, timeout=120) as response:
            zip_bytes = response.read()
            
        print(f"  Successfully downloaded {len(zip_bytes)} bytes. Extracting Shona file...")
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
            # Find files ending in '.sn'
            sn_file_name = next((name for name in archive.namelist() if name.endswith(".sn")), None)
            if not sn_file_name:
                print(f"  WARNING: No Shona (.sn) file found in the archive! Files: {archive.namelist()}")
                return 0, 0
                
            print(f"  Found Shona file: {sn_file_name}. Processing and filtering...")
            file_bytes = archive.read(sn_file_name)
            lines, tokens = clean_and_process_sn_file(file_bytes, out_file, shona_dict)
            print(f"  Extraction complete: Saved {lines} lines, ~{tokens:,} tokens.")
            return lines, tokens
            
    except Exception as e:
        print(f"  FAILED to process {url}: {e}")
        return 0, 0

def main():
    print("Step 6 — Starting Direct OPUS Download & Extraction Pipeline...")
    
    # Ensure target directories exist
    raw_dir = Path("data/raw/opus")
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path = raw_dir / "opus_shona.txt"
    
    # Load dictionary
    dict_path = "data/dictionaries/shona_words.txt"
    shona_dict = load_dictionary(dict_path)
    if not shona_dict:
        print("ERROR: Dictionary could not be loaded. Exiting.")
        return
        
    # Standard parallel zip URLs found
    urls = [
        "https://object.pouta.csc.fi/OPUS-bible-uedin/v1/moses/en-sn.txt.zip",
        "https://object.pouta.csc.fi/OPUS-CCAligned/v1/moses/en-sn.txt.zip"
    ]
    
    total_lines = 0
    total_tokens = 0
    
    with open(output_path, "w", encoding="utf-8") as out_file:
        for url in urls:
            lines, tokens = download_and_extract_corpus(url, out_file, shona_dict)
            total_lines += lines
            total_tokens += tokens
            
    print("\n" + "="*50)
    print("         DIRECT OPUS CORPORES SUMMARY")
    print("="*50)
    print(f"Total valid lines saved:      {total_lines}")
    print(f"Total Shona tokens collected: ~{total_tokens:,}")
    print(f"Output saved to:              {output_path}")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
