import os
import sys

def main():
    if sys.platform.startswith("win"):
        sys.stdout.reconfigure(encoding='utf-8')

    repo_dir = "Working_with_shona-slang"
    files = [
        'downsampled_chitchat_dataset.csv',
        'shona_combined_dataset.csv',
        'slang_dataset_with_contexts_and_intent.csv',
        'slang_dataset_with_intent.csv'
    ]

    for f_name in files:
        f_path = os.path.join(repo_dir, f_name)
        if not os.path.exists(f_path):
            print(f"\n[WARNING] {f_name} does not exist!")
            continue

        try:
            # Count lines
            line_count = 0
            with open(f_path, "r", encoding="utf-8", errors="ignore") as f:
                for _ in f:
                    line_count += 1

            # Read first 20 lines
            first_20 = []
            with open(f_path, "r", encoding="utf-8", errors="ignore") as f:
                for _ in range(20):
                    line = f.readline()
                    if not line:
                        break
                    first_20.append(line.strip())

            print(f"\n==================================================")
            print(f"FILE: {f_name}")
            print(f"Total Lines: {line_count}")
            print(f"==================================================")
            print("First 20 lines:")
            for idx, line in enumerate(first_20):
                print(f"{idx+1}: {line}")
            print("==================================================")

        except Exception as e:
            print(f"Error reading {f_name}: {e}")

if __name__ == "__main__":
    main()
