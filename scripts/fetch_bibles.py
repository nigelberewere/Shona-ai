import os
import re
import zipfile
import gzip
import io
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# Ensure directories exist
os.makedirs("data/raw/bible", exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_verse(line):
    """
    Strips verse numbers and headers to keep only the actual verse text.
    Removes patterns like:
    - 1:1
    - Gen 1:1, Genesis 1:1, 1 Kor 1:1, 1Kor 1:1
    - [1], (1)
    - Punctuation/markup artifacts
    """
    text = line.strip()
    if not text:
        return ""
    
    # 1. Remove references like "Gen 1:1" or "Genesis 1:1" or "1 Kor 1:1" at the start
    # e.g. "Genesis 1:1 In the beginning..." -> "In the beginning..."
    # We match: optional digits (for 1 Kor), optional space, letters, optional space, digits, colon, digits, followed by optional space/punctuation
    text = re.sub(r'^(?:\d+\s+)?[A-Za-z\u00C0-\u017F]+\s+\d+:\d+\s*', '', text)
    
    # 2. Remove standard verse references like "1:1 " or "12:34 " at the start
    text = re.sub(r'^\d+:\d+\s*', '', text)
    
    # 3. Remove bracketed verse numbers like "[1]" or "(1)" or "1." at the start
    text = re.sub(r'^\[\d+\]\s*', '', text)
    text = re.sub(r'^\(\d+\)\s*', '', text)
    text = re.sub(r'^\d+\.\s*', '', text)
    text = re.sub(r'^v\d+\s*', '', text)
    
    # Strip whitespace again
    text = text.strip()
    return text

def download_file(url, desc):
    try:
        print(f"Downloading {desc} from {url}...")
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r.content
        else:
            print(f"Failed to download {desc}: HTTP {r.status_code}")
    except Exception as e:
        print(f"Error downloading {desc}: {e}")
    return None

def fetch_target_1_ebible():
    """Target 1: ebible.org zips"""
    texts = []
    # Try the snk_readaloud.zip first
    for code in ["snk", "sna"]:
        zip_url = f"https://ebible.org/Scriptures/{code}_readaloud.zip"
        content = download_file(zip_url, f"ebible.org {code} zip")
        if content:
            print(f"Successfully downloaded ebible.org {code} zip!")
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as z:
                    for filename in z.namelist():
                        if filename.endswith(".txt") or filename.endswith(".usfm"):
                            with z.open(filename) as f:
                                # Try decoding as utf-8 or latin-1
                                text_content = f.read().decode('utf-8', errors='ignore')
                                for line in text_content.splitlines():
                                    cleaned = clean_verse(line)
                                    if cleaned and len(cleaned) >= 20:
                                        texts.append(cleaned)
                print(f"Extracted {len(texts)} lines from {code}_readaloud.zip")
            except Exception as e:
                print(f"Error extracting zip: {e}")
            break # If one succeeds, we can still try the other or stop
            
    # Try checking details pages if zip fails or to get more info
    # We can also parse the details.php to find text/epub links if zip didn't exist
    return texts

def fetch_target_2_christos():
    """Target 2: Christos Shona Bible"""
    texts = []
    url = "https://christos.com/shona/"
    print(f"Checking Christos at {url}...")
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Let's search for links containing "bible", "download", ".txt", ".zip", ".pdf"
            links = soup.find_all('a')
            print(f"Found {len(links)} links on Christos page.")
            for link in links:
                href = link.get('href', '')
                text = link.get_text()
                if any(x in href.lower() or x in text.lower() for x in ['.zip', '.txt', 'download', 'bible']):
                    print(f"Potential Bible link found: {href} ({text})")
        else:
            print(f"Christos page returned HTTP {r.status_code}")
    except Exception as e:
        print(f"Error checking Christos: {e}")
    return texts

def fetch_target_3_bible_gateway():
    """Target 3: Bible Gateway scraping"""
    # Let's do a quick best-effort scrape of a couple of books or chapters to see if we can get text
    # BDZE, SNK, BDS
    # For a full scrape this would be slow/blocked, but we can attempt a check
    texts = []
    # Let's try Genesis 1 in BDZE
    sample_url = "https://www.biblegateway.com/passage/?search=Genesis+1&version=BDZE"
    print(f"Checking Bible Gateway sample: {sample_url}...")
    try:
        r = requests.get(sample_url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Look for verse elements (often have class "text")
            verses = soup.find_all(class_='text')
            print(f"Found {len(verses)} text elements on Bible Gateway Genesis 1.")
            for v in verses[:5]:
                print(f"Sample verse text: {v.get_text().strip()}")
        else:
            print(f"Bible Gateway returned HTTP {r.status_code}")
    except Exception as e:
        print(f"Error checking Bible Gateway: {e}")
    return texts

def fetch_target_4_opus():
    """Target 4: OPUS Bible corpus"""
    texts = []
    urls = [
        "https://opus.nlpl.eu/download.php?f=bible-uedin/v1/mono/sn.txt.gz",
        "https://object.pouta.csc.fi/OPUS-bible-uedin/v1/mono/sn.txt.gz",
    ]
    for url in urls:
        content = download_file(url, "OPUS Bible Sn")
        if content:
            print("Successfully downloaded OPUS Bible Sn!")
            try:
                with gzip.open(io.BytesIO(content), 'rt', encoding='utf-8') as f:
                    for line in f:
                        cleaned = clean_verse(line)
                        if cleaned and len(cleaned) >= 20:
                            texts.append(cleaned)
                print(f"Extracted {len(texts)} lines from OPUS Bible Sn")
                return texts
            except Exception as e:
                print(f"Error decompressing OPUS Bible: {e}")
    return texts

def main():
    all_bible_verses = []
    
    # Run all target downloads
    t4_verses = fetch_target_4_opus()
    if t4_verses:
        all_bible_verses.extend(t4_verses)
        
    t1_verses = fetch_target_1_ebible()
    if t1_verses:
        all_bible_verses.extend(t1_verses)
        
    t2_verses = fetch_target_2_christos()
    if t2_verses:
        all_bible_verses.extend(t2_verses)
        
    t3_verses = fetch_target_3_bible_gateway()
    if t3_verses:
        all_bible_verses.extend(t3_verses)
        
    # Deduplicate the collected verses
    unique_verses = list(dict.fromkeys(all_bible_verses))
    print(f"Total raw lines collected: {len(all_bible_verses)}")
    print(f"Total unique clean lines: {len(unique_verses)}")
    
    if unique_verses:
        # Save to data/raw/bible/shona_bible_v2.txt
        output_file = "data/raw/bible/shona_bible_v2.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            for verse in unique_verses:
                f.write(verse + "\n")
        print(f"Saved {len(unique_verses)} verses to {output_file}")
        
        # Show 10 sample lines to verify quality
        print("\n--- 10 Sample Lines from shona_bible_v2.txt ---")
        sample_size = min(10, len(unique_verses))
        for i in range(sample_size):
            print(f"{i+1}: {unique_verses[i]}")
            
        # Report total lines and tokens
        word_count = sum(len(line.split()) for line in unique_verses)
        # Token estimation (rough 1.15 to 1.5 tokens per word)
        print(f"\nTotal lines: {len(unique_verses)}")
        print(f"Estimated Word Count: {word_count}")
    else:
        print("No Bible verses were successfully downloaded.")

if __name__ == "__main__":
    main()
