import urllib.request
import urllib.error
import re
import sys

def test_sitemap():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    urls = [
        "https://www.voashona.com/sitemap.xml",
        "https://www.voashona.com/sitemap-news.xml",
        "https://www.voashona.com/archive",
        "https://www.voashona.com/z/4797?p=20",
        "https://www.voashona.com/z/4797?p=50",
    ]
    
    for url in urls:
        print(f"\nFetching {url}...")
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode('utf-8', errors='ignore')
                print(f"  Success! Content length: {len(content)} bytes.")
                if "xml" in url:
                    # Look for URLs
                    urls_found = re.findall(r'<loc>(.*?)</loc>', content)
                    print(f"  Found {len(urls_found)} URLs in XML.")
                    if urls_found:
                        print(f"  First 3 URLs: {urls_found[:3]}")
                else:
                    # Look for standard pagination signs or article links
                    article_links = re.findall(r'href=["\'](/a/[^"\']+\.html)["\']', content)
                    print(f"  Found {len(article_links)} article links on the page.")
        except urllib.error.HTTPError as e:
            print(f"  HTTP Error {e.code}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_sitemap()
