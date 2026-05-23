import urllib.request
import urllib.error
import re
import time
import os
import sys
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

def clean_html(text):
    """
    Removes HTML tags from text.
    """
    return re.sub(r'<[^>]*>', '', text)

def check_shona_ratio(line, shona_dict):
    """
    Checks if a line meets the Shona word ratio constraint.
    At most 30% of the words should be absent from the Shona dictionary (70% or more must be present).
    """
    # Simple word tokenization: find all alphabetic character strings
    words = re.findall(r'[a-z]+', line.lower())
    if not words:
        return False
        
    absent_count = 0
    for w in words:
        if w not in shona_dict:
            absent_count += 1
            
    ratio = absent_count / len(words)
    # Ratio of non-Shona words must be <= 30%
    return ratio <= 0.30

def fetch_html(url, headers):
    """
    Fetches HTML content for a URL using urllib.request.
    """
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8', errors='ignore')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Silence 404s since some pagination indices might be out of range
            pass
        else:
            print(f"  HTTP Error {e.code} for {url}")
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
    return None

def main():
    print("Step 2 — Initializing VOA Zimbabwe Shona scraper...")
    
    # 1. Setup paths
    dict_path = "data/dictionaries/shona_words.txt"
    raw_dir = Path("data/raw/voa")
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path = raw_dir / "voa_shona.txt"
    
    # Load dictionary
    shona_dict = load_dictionary(dict_path)
    if not shona_dict:
        print("ERROR: Dictionary could not be loaded. Exiting.")
        sys.exit(1)
        
    # Standard headers for user agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # 2. Collect unique article URLs
    # Categories listed on voashona.com main page
    categories = [
        "3191", "3192", "3194", "3197", "3198", "3200", "3205", "3259", "3346", "3887", "4758", "4766"
    ]
    
    article_urls = set()
    print("Collecting article URLs from categories (paginating)...")
    
    for cat in categories:
        cat_url_count = 0
        # Iterate over pagination index (p=0, 1, 2, ... 15)
        for p in range(16):
            url = f"https://www.voashona.com/z/{cat}?p={p}"
            html = fetch_html(url, headers)
            if not html:
                break
                
            # Find links of the form href="/a/..." or "/a/....html"
            links = re.findall(r'href=["\'](/a/[^"\']+\.html)["\']', html)
            if not links:
                break
                
            new_links_found = 0
            for link in links:
                full_link = f"https://www.voashona.com{link}"
                if full_link not in article_urls:
                    article_urls.add(full_link)
                    new_links_found += 1
                    cat_url_count += 1
                    
            # If no new links were found on this pagination page, we can stop paginating this category
            if new_links_found == 0:
                break
                
            time.sleep(0.5) # small sleep between list fetches
            
        print(f"  Category {cat}: Collected {cat_url_count} unique article links.")
        
    total_articles = len(article_urls)
    print(f"\nTotal unique VOA Shona articles collected: {total_articles}")
    
    if total_articles == 0:
        print("ERROR: No article URLs collected! Exiting.")
        sys.exit(1)
        
    # 3. Scrape and clean articles
    scraped_count = 0
    total_lines_written = 0
    total_tokens_collected = 0
    
    print(f"Scraping articles one-by-one. Output file: {output_path}...")
    
    # Open output file in append mode (or write mode)
    with open(output_path, "w", encoding="utf-8") as out_file:
        for idx, url in enumerate(article_urls):
            scraped_count += 1
            
            # Fetch article html
            html = fetch_html(url, headers)
            if not html:
                time.sleep(1)
                continue
                
            # Extract content inside <div class="wsw"> (standard VOA content body class)
            wsw_match = re.search(r'<div[^>]*class=["\'][^"\']*wsw[^"\']*["\'][^>]*>(.*?)</div>', html, re.DOTALL)
            
            p_contents = []
            if wsw_match:
                # Find all <p> tags inside class="wsw"
                p_tags = re.findall(r'<p>(.*?)</p>', wsw_match.group(1), re.DOTALL)
                p_contents = p_tags
            else:
                # Fallback: find all <p> tags in the whole document
                p_tags = re.findall(r'<p>(.*?)</p>', html, re.DOTALL)
                # Keep only longer p tags to avoid layout clutter
                p_contents = [p for p in p_tags if len(p) > 50]
                
            # Process each paragraph
            article_lines_written = 0
            for p in p_contents:
                cleaned_text = clean_html(p)
                # Normalize whitespaces
                cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
                
                # Split into sentences for finer filtering
                sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
                for sentence in sentences:
                    sentence = sentence.strip()
                    # Filter: line must be >= 20 characters
                    if len(sentence) < 20:
                        continue
                        
                    # Filter: Shona word ratio check (at most 30% not in dictionary)
                    if not check_shona_ratio(sentence, shona_dict):
                        continue
                        
                    # Write line
                    out_file.write(sentence + "\n")
                    article_lines_written += 1
                    total_lines_written += 1
                    total_tokens_collected += len(sentence.split())
                    
            # Print progress every 50 articles
            if scraped_count % 50 == 0 or scraped_count == total_articles:
                print(f"  Scraped {scraped_count}/{total_articles} articles. Lines written: {total_lines_written} | Tokens collected: ~{total_tokens_collected:,}")
                
            # Rate limiting
            time.sleep(1.0)
            
    print("\n" + "="*50)
    print("            VOA SHONA SCRAPER SUMMARY")
    print("="*50)
    print(f"Articles attempted/scraped: {scraped_count}")
    print(f"Total valid lines saved:    {total_lines_written}")
    print(f"Total Shona tokens collected: ~{total_tokens_collected:,}")
    print(f"Output saved to:            {output_path}")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
