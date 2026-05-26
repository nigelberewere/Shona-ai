import os
import sys

def main():
    if sys.platform.startswith("win"):
        sys.stdout.reconfigure(encoding='utf-8')

    repo_dir = os.path.join("cloned", "shona-spacy")
    
    files = [
        ("shona_tokens_with_classes.csv", repo_dir),
        ("shona_lexicon.json", os.path.join(repo_dir, "shona_spacy", "data"))
    ]

    for f_name, f_dir in files:
        f_path = os.path.join(f_dir, f_name)
        if not os.path.exists(f_path):
            print(f"\n[WARNING] {f_name} does not exist at {f_path}!")
            continue

        try:
            # Count lines
            line_count = 0
            with open(f_path, "r", encoding="utf-8", errors="ignore") as f:
                for _ in f:
                    line_count += 1

            # Read first 10 lines
            first_10 = []
            with open(f_path, "r", encoding="utf-8", errors="ignore") as f:
                for _ in range(10):
                    line = f.readline()
                    if not line:
                        break
                    first_10.append(line.strip())

            print(f"\n==================================================")
            print(f"FILE: {f_name}")
            print(f"Total Lines: {line_count}")
            print(f"==================================================")
            print("First 10 lines:")
            for idx, line in enumerate(first_10):
                print(f"{idx+1}: {line}")
            print("==================================================")

        except Exception as e:
            print(f"Error reading {f_name}: {e}")

if __name__ == "__main__":
    main()
