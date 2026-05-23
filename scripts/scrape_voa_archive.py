import urllib.request
import urllib.error
import re
import time
import os
import sys
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

def load_dictionary(dict_path):
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
        
    corpus_path = "data/processed/all_clean.txt"
    if os.path.exists(corpus_path):
        print(f"Loading Shona words from corpus {corpus_path}...")
        try:
            with open(corpus_path, "r", encoding="utf-8") as f:
                content = f.read().lower()
                corpus_words = set(re.findall(r'[a-z]+', content))
            words.update(corpus_words)
            print(f"Total vocabulary size: {len(words)}")
        except Exception as e:
            print(f"WARNING: Failed to load words from corpus: {e}")
            
    return words

def clean_html(text):
    return re.sub(r'<[^>]*>', '', text)

def check_shona_ratio(line, shona_dict):
    words = re.findall(r'[a-z]+', line.lower())
    if not words:
        return False
    absent_count = sum(1 for w in words if w not in shona_dict)
    ratio = absent_count / len(words)
    return ratio <= 0.30

def fetch_html(url, headers):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception:
        pass
    return None

def process_article(url, headers, shona_dict):
    html = fetch_html(url, headers)
    if not html:
        return []
        
    wsw_match = re.search(r'<div[^>]*class=["\'][^"\']*wsw[^"\']*["\'][^>]*>(.*?)</div>', html, re.DOTALL)
    p_contents = []
    if wsw_match:
        p_tags = re.findall(r'<p>(.*?)</p>', wsw_match.group(1), re.DOTALL)
        p_contents = p_tags
    else:
        p_tags = re.findall(r'<p>(.*?)</p>', html, re.DOTALL)
        p_contents = [p for p in p_tags if len(p) > 50]
        
    sentences_written = []
    for p in p_contents:
        cleaned_text = clean_html(p)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            if not check_shona_ratio(sentence, shona_dict):
                continue
            sentences_written.append(sentence)
            
    return sentences_written

def main():
    print("=== VOA Shona Historical Scraper Sprint ===")
    
    dict_path = "data/dictionaries/shona_words.txt"
    shona_dict = load_dictionary(dict_path)
    if not shona_dict:
        print("ERROR: Dictionary could not be loaded. Exiting.")
        sys.exit(1)
        
    sitemap_path = "data/raw/voa/sitemap_urls.txt"
    if not os.path.exists(sitemap_path):
        print(f"ERROR: Sitemap file {sitemap_path} not found! Run scrape_voa_sitemaps.py first.")
        sys.exit(1)
        
    with open(sitemap_path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
        
    print(f"Loaded {len(urls):,} potential article URLs.")
    
    # We will sample 6,000 URLs randomly to get a broad slice of history
    # Set seed for reproducibility
    random.seed(2026)
    sample_size = min(6000, len(urls))
    sampled_urls = random.sample(urls, sample_size)
    print(f"Sampled {sample_size} articles for deeper archive scrape.")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    raw_dir = Path("data/raw/voa")
    output_path = raw_dir / "voa_shona_archive_2.txt"
    
    scraped_lines = []
    completed_count = 0
    success_count = 0
    
    print(f"Scraping articles concurrently using 40 threads...")
    
    with ThreadPoolExecutor(max_workers=40) as executor:
        futures = {executor.submit(process_article, url, headers, shona_dict): url for url in sampled_urls}
        
        for future in as_completed(futures):
            completed_count += 1
            url = futures[future]
            try:
                sentences = future.result()
                if sentences:
                    scraped_lines.extend(sentences)
                    success_count += 1
            except Exception as e:
                # Silently ignore errors to keep progress clean
                pass
                
            if completed_count % 100 == 0 or completed_count == sample_size:
                percentage = (completed_count / sample_size) * 100
                total_tokens = sum(len(l.split()) for l in scraped_lines)
                print(f"Progress: {completed_count}/{sample_size} ({percentage:.1f}%) | Success articles: {success_count} | Lines: {len(scraped_lines):,} | Est. Tokens: {total_tokens:,}")
                
    # Deduplicate lines
    unique_lines = list(dict.fromkeys(scraped_lines))
    print(f"\nDeduplicated lines: {len(scraped_lines):,} -> {len(unique_lines):,}")
    
    total_tokens = sum(len(l.split()) for l in unique_lines)
    print(f"Total Shona tokens collected: {total_tokens:,}")
    
    print(f"Saving to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        for line in unique_lines:
            f.write(line + "\n")
            
    print("VOA Archive Scrape Sprint Complete!")

if __name__ == "__main__":
    main()
