import urllib.request
import json
import zipfile
import io
import os

def main():
    print("Fetching metadata for shona-spacy from PyPI...")
    url = "https://pypi.org/pypi/shona-spacy/json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
        version = data.get("info", {}).get("version", "0.1.5")
        print(f"Latest version is {version}")
        
        releases = data.get("releases", {})
        version_releases = releases.get(version, [])
        
        wheel_url = None
        for r in version_releases:
            if r.get("packagetype") == "bdist_wheel":
                wheel_url = r.get("url")
                break
                
        if not wheel_url:
            # Fallback to any wheel or tar.gz
            for v in sorted(releases.keys(), reverse=True):
                for r in releases[v]:
                    if r.get("packagetype") == "bdist_wheel":
                        wheel_url = r.get("url")
                        version = v
                        print(f"Fallback to version {version} wheel")
                        break
                if wheel_url:
                    break
                    
        if not wheel_url:
            print("No wheel found in PyPI releases!")
            return
            
        print(f"Downloading wheel from: {wheel_url}")
        wheel_req = urllib.request.Request(wheel_url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(wheel_req) as wheel_response:
            wheel_data = wheel_response.read()
            
        print("Successfully downloaded wheel. Extracting shona_lexicon.json...")
        with zipfile.ZipFile(io.BytesIO(wheel_data)) as z:
            # Find the path of shona_lexicon.json inside the wheel
            lexicon_path = None
            for name in z.namelist():
                if name.endswith("shona_lexicon.json"):
                    lexicon_path = name
                    break
                    
            if not lexicon_path:
                print("Could not find shona_lexicon.json in the package!")
                print("Available files:")
                for name in z.namelist()[:20]:
                    print(f"  {name}")
                return
                
            print(f"Found lexicon at: {lexicon_path}")
            lexicon_content = z.read(lexicon_path).decode('utf-8')
            
            # Load and re-save cleanly in local workspace
            lexicon_data = json.loads(lexicon_content)
            print(f"Loaded lexicon containing {len(lexicon_data)} entries.")
            
            output_path = "shona_lexicon.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(lexicon_data, f, ensure_ascii=False, indent=2)
            print(f"Saved Shona spaCy lexicon to local workspace at {output_path}!")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
