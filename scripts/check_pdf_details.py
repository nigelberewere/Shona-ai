import pdfplumber
import re

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def main():
    pdf_path = "data/raw/books/Fivaz & Ratzlaff - Shona Language Lessons, New Edition.pdf"
    
    print("Checking PDF details...")
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages in PDF: {total_pages}")
        
        # 1. Check pages 20, 40, 60, 80 (1-indexed, so indices 19, 39, 59, 79)
        target_pages = [20, 40, 60, 80]
        for p_num in target_pages:
            idx = p_num - 1
            page = pdf.pages[idx]
            text = page.extract_text()
            if text:
                print(f"\n=== PAGE {p_num} (first 200 chars) ===")
                print(text[:200])
            else:
                print(f"\n=== PAGE {p_num} ===")
                print("No extractable text")
                
        # 2. Heuristics for stats across all pages
        extractable_count = 0
        table_like_pages = 0
        sentence_like_pages = 0
        
        all_sentences = []
        
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            
            extractable_count += 1
            
            # Simple heuristic to distinguish grammar tables vs actual sentences:
            # - If a page has many columns separated by spaces, tabs, or dashes (like 'mu- va-', 'chi- zvi-'), it's a table.
            # - If it contains standard punctuation (periods, question marks) and longer word sequences, it's sentences.
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if not lines:
                continue
                
            table_lines = 0
            sentence_lines = 0
            
            for line in lines:
                # Look for typical Shona complete sentences (starts with uppercase, ends with punctuation, contains standard Shona words)
                # Shona words commonly end in vowels: a, e, i, o, u
                if re.search(r'^[A-Z].*[.!?]$', line) and len(line.split()) >= 4:
                    sentence_lines += 1
                    # Save potential good sentences
                    all_sentences.append((i+1, line))
                elif re.search(r'[-–—]\s+[a-z]', line) or len(re.findall(r'\s{3,}', line)) >= 2:
                    table_lines += 1
            
            if table_lines > sentence_lines:
                table_like_pages += 1
            else:
                sentence_like_pages += 1
                
        print(f"\n=== STATS ===")
        print(f"Total extractable pages: {extractable_count} / {total_pages}")
        print(f"Pages matching grammar/vocab tables: {table_like_pages}")
        print(f"Pages matching actual Shona sentences/prose: {sentence_like_pages}")
        
        # 3. Find the best 5 complete Shona sentences
        # Let's filter for sentences that have only valid letters/spaces/punctuation (no numbers, no English translations)
        # Often in the textbook, Shona sentences are followed by English translations. Let's find pure Shona sentences.
        shona_sentences = []
        for p_num, sentence in all_sentences:
            # Clean sentence
            s_clean = sentence.strip()
            # Heuristic for pure Shona sentence:
            # - Must not contain English words like "the", "and", "is", "of", "to", "you", "he", "she", "it" (case-insensitive)
            # - Must consist of Shona-like syllables
            words = s_clean.split()
            english_words = {"the", "and", "is", "of", "to", "you", "he", "she", "it", "was", "were", "in", "on", "at", "by", "for", "with", "a", "an"}
            if any(w.lower() in english_words for w in words):
                continue
            if len(s_clean) >= 30 and len(s_clean) <= 120:
                shona_sentences.append((p_num, s_clean))
                
        # Deduplicate
        unique_sentences = list(dict.fromkeys([s for p, s in shona_sentences]))
        
        print(f"\n=== BEST COMPLETE SHONA SENTENCES FOUND ({len(unique_sentences)} total candidates) ===")
        for idx, s in enumerate(unique_sentences[:5]):
            print(f"{idx+1}: {s}")

if __name__ == "__main__":
    main()
