import re
import os

def clean_opus():
    input_path = "data/raw/opus/opus_shona.txt"
    output_path = "data/raw/opus/opus_shona_clean.txt"
    
    if not os.path.exists(input_path):
        print(f"ERROR: {input_path} not found!")
        return
        
    print(f"Loading raw OPUS Shona lines from {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    # Keep lines that are clean Shona prose:
    # - No English stopwords appearing more than once
    # - No product names, prices, technical jargon
    english_signals = [
        "disbelievers", "sterilized", "saline", "injection", "diluted",
        "blockchain", "bitcoin", "crypto", "USB", "PDF", "LED", "LCD",
        "download", "upload", "software", "hardware", "database",
        "certificate", "university", "college", "degree",
    ]

    def is_clean(line):
        line_lower = line.lower()
        # Reject lines with technical English signals
        for signal in english_signals:
            if signal in line_lower:
                return False
        # Reject lines where more than 2 words are purely ASCII uppercase (acronyms)
        words = line.split()
        upper_count = sum(1 for w in words if w.isupper() and len(w) > 1)
        if upper_count > 2:
            return False
        # Reject lines shorter than 20 chars
        if len(line) < 20:
            return False
        return True

    clean_lines = [l for l in lines if is_clean(l)]
    print(f"Before: {len(lines)}, After: {len(clean_lines)}")

    print(f"Writing cleaned OPUS lines to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(clean_lines))

if __name__ == "__main__":
    clean_opus()
