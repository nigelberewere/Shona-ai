import os
import sys
import re
from pathlib import Path
import pdfplumber
import docx

def safe_print(msg):
    try:
        print(msg)
    except Exception:
        try:
            print(msg.encode('ascii', errors='replace').decode('ascii'))
        except Exception:
            pass

def is_garbled_or_empty(text):
    if not text or not text.strip():
        return True
    letters = sum(1 for c in text if c.isalpha())
    if len(text) > 0 and letters / len(text) < 0.40:
        return True
    return False

def extract_pdf(pdf_path, extracted_dir):
    name = pdf_path.name
    safe_print(f"\nProcessing PDF: {name}")
    try:
        raw_pages = []
        with pdfplumber.open(pdf_path) as pdf:
            safe_print(f"  Total pages: {len(pdf.pages)}")
            for idx, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    raw_pages.append(text)
        
        full_text = "\n".join(raw_pages)
        if is_garbled_or_empty(full_text):
            safe_print(f"  RESULT: OCR-locked or empty. Skipping.")
            return None, 0
            
        sample_chars = full_text[:200].replace("\n", " ")
        safe_print(f"  First 200 characters:\n  [SAMPLE] {sample_chars}...")
        
        filename_without_ext = pdf_path.stem.lower().replace(" ", "_")
        target_path = extracted_dir / f"{filename_without_ext}.txt"
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        lines_count = len(full_text.splitlines())
        safe_print(f"  RESULT: Successfully extracted {lines_count:,} raw lines. Saved to {target_path.name}")
        return target_path, lines_count
        
    except Exception as e:
        if "Password" in str(e) or "password" in str(e).lower() or "PDFPasswordIncorrect" in str(type(e)):
            safe_print(f"  RESULT: Password-protected / encrypted. Skipping.")
        else:
            safe_print(f"  FAILED to process PDF {name}: {e}")
        return None, 0

def extract_docx(docx_path, extracted_dir):
    name = docx_path.name
    safe_print(f"\nProcessing DOCX: {name}")
    try:
        doc = docx.Document(docx_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n".join(paragraphs)
        
        if is_garbled_or_empty(full_text):
            safe_print(f"  RESULT: OCR-locked or empty. Skipping.")
            return None, 0
            
        sample_chars = full_text[:200].replace("\n", " ")
        safe_print(f"  First 200 characters:\n  [SAMPLE] {sample_chars}...")
        
        filename_without_ext = docx_path.stem.lower().replace(" ", "_")
        target_path = extracted_dir / f"{filename_without_ext}.txt"
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        lines_count = len(full_text.splitlines())
        safe_print(f"  RESULT: Successfully extracted {lines_count:,} raw paragraphs. Saved to {target_path.name}")
        return target_path, lines_count
        
    except Exception as e:
        safe_print(f"  FAILED to process DOCX {name}: {e}")
        return None, 0

def main():
    safe_print("=== Phase 2 — Shona O-Level Study Materials Extraction ===")
    
    shona_dir = Path("data/raw/SHONA")
    if not shona_dir.exists():
        safe_print(f"ERROR: Directory {shona_dir} does not exist.")
        return
        
    extracted_dir = shona_dir / "extracted"
    extracted_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(shona_dir.glob("*.pdf"))
    docx_files = list(shona_dir.glob("*.docx"))
    
    safe_print(f"Found {len(pdf_files)} PDF files and {len(docx_files)} DOCX files in {shona_dir}")
    
    extracted_registry = []
    
    for pdf in pdf_files:
        path, lines = extract_pdf(pdf, extracted_dir)
        if path:
            extracted_registry.append((pdf.name, path, lines))
            
    for docx_file in docx_files:
        path, lines = extract_docx(docx_file, extracted_dir)
        if path:
            extracted_registry.append((docx_file.name, path, lines))
            
    safe_print("\n" + "="*60)
    safe_print("               RAW EXTRACTION SAMPLES (Step 3)")
    safe_print("="*60)
    for original_name, path, lines in extracted_registry:
        safe_print(f"\nFile name: {original_name}")
        safe_print(f"Number of lines extracted: {lines:,}")
        
        with open(path, "r", encoding="utf-8") as f:
            content_lines = [l.strip() for l in f if l.strip()]
        
        safe_print("First 3 lines of content:")
        for idx, line in enumerate(content_lines[:3]):
            safe_print(f"  Line {idx+1}: {line}")
            
    safe_print("="*60 + "\n")

if __name__ == "__main__":
    main()
