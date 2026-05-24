import os
import sys
import tarfile
import urllib.request
import ssl
from pathlib import Path
import re

# Insert parent directory so we can import scripts.clean_data
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.clean_data import is_probably_shona, clean_candidate

def download_file(url, target_path):
    print(f"Downloading Leipzig corpus from: {url}...")
    headers = {"User-Agent": "Mozilla/5.0"}
    context = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=context, timeout=120) as response:
            with open(target_path, "wb") as f:
                f.write(response.read())
        print(f"Downloaded successfully to {target_path} ({os.path.getsize(target_path):,} bytes).")
        return True
    except Exception as e:
        print(f"FAILED to download from {url}: {e}")
        return False

def extract_and_clean(tar_path, output_path):
    print(f"Extracting sentences file from {tar_path}...")
    
    # We want to extract 'sna-zw_web_2018_100K/sna-zw_web_2018_100K-sentences.txt'
    sentences_file_name = None
    
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name.endswith("-sentences.txt"):
                sentences_file_name = member.name
                break
        
        if not sentences_file_name:
            print("ERROR: Could not find any sentences.txt file in the tar.gz package.")
            return 0, 0
            
        print(f"Found sentences file in archive: {sentences_file_name}")
        f_obj = tar.extractfile(sentences_file_name)
        if not f_obj:
            print("ERROR: Failed to extract sentences file.")
            return 0, 0
            
        text_bytes = f_obj.read()
        
    print("Parsing and cleaning sentences...")
    text_content = text_bytes.decode("utf-8", errors="ignore")
    lines = text_content.splitlines()
    print(f"Total raw lines in sentences file: {len(lines):,}")
    
    technical_words = {
        "helical", "compression", "torsion", "caffeine", "dmaa", "http", "usb",
        "blockchain", "bitcoin", "crypto", "pdf", "led", "lcd", "download",
        "upload", "software", "hardware", "database", "university", "college",
        "www", ".com", ".org", ".net"
    }
    
    clean_lines = []
    skipped_wiki = 0
    skipped_code = 0
    skipped_technical = 0
    skipped_short = 0
    skipped_not_shona = 0
    
    for line in lines:
        if not line.strip():
            continue
        parts = line.split("\t", 1)
        if len(parts) < 2:
            continue
        sentence_id, sentence = parts
        
        # Initial candidate cleaning
        sentence = clean_candidate(sentence)
        
        # Check rule: wiki markup & special chars
        if any(char in sentence for char in ['[', ']', '{', '}', '<', '>', '|', '\\', '/']):
            skipped_wiki += 1
            continue
            
        if sentence.startswith("*") or sentence.startswith("#"):
            skipped_wiki += 1
            continue
            
        # Reject programming operators
        if " = " in sentence or " ~= " in sentence or " == " in sentence or "local " in sentence or "function " in sentence:
            skipped_code += 1
            continue
            
        # Reject technical terms / URLs / English terms
        sentence_lower = sentence.lower()
        contains_tech = False
        for tech in technical_words:
            if tech in sentence_lower:
                contains_tech = True
                break
        if contains_tech:
            skipped_technical += 1
            continue
            
        # Truncated sentences ending in ...
        if sentence.endswith("...") or sentence.endswith("..") or sentence.endswith(". . ."):
            skipped_technical += 1
            continue
            
        # Rejected short sentences
        if len(sentence) < 20:
            skipped_short += 1
            continue
            
        # Language detection and Shona lexical scoring
        if not is_probably_shona(sentence):
            skipped_not_shona += 1
            continue
            
        clean_lines.append(sentence)
        
    # Deduplicate
    unique_lines = list(dict.fromkeys(clean_lines))
    
    total_lines = len(unique_lines)
    total_tokens = sum(len(l.split()) for l in unique_lines)
    
    print("\nLeipzig Corpus Cleaning Statistics:")
    print(f"  Skipped wiki markup & special chars: {skipped_wiki:,}")
    print(f"  Skipped code / programming syntax:  {skipped_code:,}")
    print(f"  Skipped technical noise & URL:      {skipped_technical:,}")
    print(f"  Skipped short lines (<20 ch):       {skipped_short:,}")
    print(f"  Skipped not Shona:                  {skipped_not_shona:,}")
    print(f"  Unique Clean Lines Retained:        {total_lines:,}")
    print(f"  Total Clean Tokens:                 {total_tokens:,}")
    
    # Save output to data/processed/leipzig_clean.txt
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as out:
        for line in unique_lines:
            out.write(line + "\n")
            
    print(f"Cleaned sentences saved to: {output_path}")
    return total_lines, total_tokens

def main():
    url = "https://downloads.wortschatz-leipzig.de/corpora/sna-zw_web_2018_100K.tar.gz"
    
    # Ensure directory structure exists
    raw_dir = Path("data/raw/leipzig")
    raw_dir.mkdir(parents=True, exist_ok=True)
    tar_path = raw_dir / "sna-zw_web_2018_100K.tar.gz"
    
    processed_dir = Path("data/processed/leipzig")
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / "leipzig_clean.txt"
    
    if not tar_path.exists():
        success = download_file(url, tar_path)
        if not success:
            print("ERROR: Download failed. Exiting.")
            return
    else:
        print(f"Leipzig archive already exists locally: {tar_path}")
        
    lines, tokens = extract_and_clean(tar_path, output_path)
    print(f"\nCompleted Leipzig processing: {lines} lines, {tokens} tokens.")

if __name__ == "__main__":
    main()
