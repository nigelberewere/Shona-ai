import pdfplumber
import re
import sys

def main():
    if sys.platform.startswith("win"):
        sys.stdout.reconfigure(encoding='utf-8')
        
    sentences = []
    pdf_path = "data/raw/books/Fivaz & Ratzlaff - Shona Language Lessons, New Edition.pdf"
    
    print("JOB: Extracting Shona sentences from PDF...")
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split('\n'):
                line = line.strip()
                # Fix diacritic corruption - digits replacing accented chars
                line = re.sub(r'([a-z])6([a-z])', r'\1o\2', line)
                line = re.sub(r'([a-z])4([a-z])', r'\1a\2', line)
                
                # Keep only lines that look like Shona sentences
                if len(line) < 15:
                    continue
                if line.isupper():
                    continue  # skip lesson headers
                if line.startswith('LESSON'):
                    continue
                if line.startswith('Write') or line.startswith('Notice'):
                    continue
                
                # Must contain at least one Shona verb marker
                shona_markers = ['ndi', 'mu', 'va', 'ku', 'chi', 'zvi', 'a', 'ti']
                words = line.lower().split()
                if not any(any(w.startswith(m) for m in shona_markers) for w in words):
                    continue
                sentences.append(line)

    print(f"Extracted: {len(sentences)} lines")
    print("\nFirst 20 samples:")
    for idx, s in enumerate(sentences[:20]):
        print(f"  {idx+1}: {s}")

if __name__ == "__main__":
    main()
