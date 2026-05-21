import random
from pathlib import Path

def main():
    lines = Path('data/processed/train.txt').read_text(encoding='utf-8').splitlines()
    print(f'Train lines: {len(lines)}')

    random.seed(42)
    sampled = random.sample(lines, min(len(lines), 30))
    print('--- SAMPLES ---')
    for line in sampled:
        print(line)

    print('--- QUALITY ---')
    english_words = {'the', 'and', 'to', 'of', 'a', 'in', 'that', 'is', 'was', 'for', 'on', 'with', 'as', 'by', 'it', 'at', 'an', 'be', 'this', 'are'}
    all_words = []
    short_lines = 0
    for line in lines:
        words = [w.lower().strip('.,!?;:"()[]{}') for w in line.split()]
        all_words.extend(words)
        if len(words) < 5:
            short_lines += 1

    english_count = sum(1 for w in all_words if w in english_words)
    contam_pct = (english_count / len(all_words)) * 100 if all_words else 0
    short_pct = (short_lines / len(lines)) * 100 if lines else 0

    print(f'English contamination: {contam_pct:.1f}%')
    print(f'Short lines (<5 words): {short_pct:.1f}%')

if __name__ == '__main__':
    main()
