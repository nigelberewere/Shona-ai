import urllib.request
import gzip
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def test_sitemaps():
    print("=== Extracting URLs from VOA Shona Sitemaps ===")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    sitemaps = [
        "https://www.voashona.com/sitemap_436_1.xml.gz",
        "https://www.voashona.com/sitemap_436_2.xml.gz"
    ]
    
    all_article_urls = set()
    
    for sitemap_url in sitemaps:
        print(f"\nDownloading {sitemap_url}...")
        req = urllib.request.Request(sitemap_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                compressed_data = response.read()
                print(f"  Downloaded {len(compressed_data):,} bytes.")
                
                # Decompress gz
                decompressed_data = gzip.decompress(compressed_data)
                print(f"  Decompressed to {len(decompressed_data):,} bytes.")
                
                # Use regex or XML parser to extract <loc> tags
                # Since XML parsing can be strict or slow, a robust regex is excellent
                urls = re.findall(r'<loc>(.*?)</loc>', decompressed_data.decode('utf-8'))
                print(f"  Found {len(urls):,} URLs.")
                
                # Filter for articles: standard articles contain "/a/" and end with ".html"
                articles = [u for u in urls if "/a/" in u and u.endswith(".html")]
                print(f"  Found {len(articles):,} article URLs.")
                
                for u in articles:
                    all_article_urls.add(u)
                    
        except Exception as e:
            print(f"  Error processing sitemap {sitemap_url}: {e}")
            
    print(f"\nTotal unique article URLs across all sitemaps: {len(all_article_urls):,}")
    
    # Save the URLs to a text file for further scraping
    urls_file = Path("data/raw/voa/sitemap_urls.txt")
    urls_file.parent.mkdir(parents=True, exist_ok=True)
    with open(urls_file, "w", encoding="utf-8") as f:
        for u in sorted(all_article_urls):
            f.write(u + "\n")
    print(f"Saved article URLs to {urls_file}")

if __name__ == "__main__":
    test_sitemaps()
