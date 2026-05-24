import urllib.request
import ssl

def test():
    url = "https://raw.githubusercontent.com/masakhane-io/masakhane-news/main/data/sna/train.tsv"
    print(f"Attempting to fetch raw URL: {url}")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=context, timeout=10) as response:
            data = response.read(200)
            print("SUCCESS!")
            print(f"Data sample: {data.decode('utf-8')}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test()
