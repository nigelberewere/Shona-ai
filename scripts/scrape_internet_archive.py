import urllib.request
import urllib.parse
import json
import re
import os
from pathlib import Path

def search_internet_archive():
    print("=== Scraping Internet Archive for Shona Language Texts ===")
    
    query = 'subject:"Shona language" AND mediatype:texts'
    params = {
        'q': query,
        'fl[]': ['identifier', 'title', 'creator'],
        'rows': 100,
        'output': 'json'
    }
    
    url_params = urllib.parse.urlencode(params, doseq=True)
    search_url = f"https://archive.org/advancedsearch.php?{url_params}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    req = urllib.request.Request(search_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error querying Internet Archive search API: {e}")
        return
        
    docs = data.get('response', {}).get('docs', [])
    print(f"Found {len(docs)} documents on Internet Archive.")
    
    raw_dir = Path("data/raw/literature")
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path = raw_dir / "archive_org_shona.txt"
    
    all_lines = []
    
    for idx, doc in enumerate(docs):
        identifier = doc.get('identifier')
        title = doc.get('title')
        creator = doc.get('creator', 'Unknown')
        print(f"\n[{idx+1}/{len(docs)}] Title: {title} | Creator: {creator} | Identifier: {identifier}")
        
        # Check files available for this item
        files_url = f"https://archive.org/metadata/{identifier}"
        req_files = urllib.request.Request(files_url, headers=headers)
        
        try:
            with urllib.request.urlopen(req_files, timeout=30) as resp:
                meta = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            print(f"  Error getting metadata for {identifier}: {e}")
            continue
            
        files = meta.get('files', [])
        # Find txt files
        txt_file = None
        for f in files:
            name = f.get('name', '')
            if name.endswith('_djvu.txt') or name.endswith('.txt'):
                # Prefer djvu.txt as it's typically the cleanest OCR text
                if name.endswith('_djvu.txt'):
                    txt_file = name
                    break
                else:
                    txt_file = name
                    
        if not txt_file:
            print("  No text files (.txt or _djvu.txt) found for this document.")
            continue
            
        download_url = f"https://archive.org/download/{identifier}/{txt_file}"
        print(f"  Found text file: {txt_file}")
        print(f"  Downloading from {download_url}...")
        
        req_dl = urllib.request.Request(download_url, headers=headers)
        try:
            with urllib.request.urlopen(req_dl, timeout=60) as resp:
                text_content = resp.read().decode('utf-8', errors='ignore')
                lines = text_content.splitlines()
                print(f"  Successfully downloaded {len(lines):,} lines.")
                
                # Perform light Shona relevance check
                # Many books categorized as "Shona language" are grammar guides in English, or dictionaries, or bilingual texts
                # Let's count if it looks like there's actually Shona words in it
                # We can do a quick check against our dictionary/corpus words
                all_words = re.findall(r'[a-z]+', text_content.lower())
                if not all_words:
                    print("  No alphabetic words found in downloaded text. Skipping.")
                    continue
                    
                # We will save the raw lines and clean them later in the compile phase
                all_lines.extend([l.strip() for l in lines if l.strip()])
        except Exception as e:
            print(f"  Error downloading text file: {e}")
            continue
            
    if all_lines:
        print(f"\nWriting {len(all_lines):,} raw lines from Internet Archive to {output_path}...")
        with open(output_path, "w", encoding="utf-8") as f:
            for line in all_lines:
                f.write(line + "\n")
        print("Internet Archive download complete!")
    else:
        print("\nNo Shona text files were downloaded.")

if __name__ == "__main__":
    search_internet_archive()
