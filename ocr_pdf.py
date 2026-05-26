import os
import io
import sys
import json
import fitz  # PyMuPDF
from PIL import Image
import easyocr

# Force standard output to support UTF-8 (essential for console printing on Windows)
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PDF_PATH = r"c:\Users\nigel\projects\Shona ai\data\raw\SHONA\O_level_Dudziramutauro_reChishona.pdf"
CHECKPOINT_PATH = r"c:\Users\nigel\projects\Shona ai\data\raw\SHONA\O_level_Dudziramutauro_reChishona_ocr_checkpoint.json"
OUTPUT_TXT_PATH = r"c:\Users\nigel\projects\Shona ai\data\raw\SHONA\O_level_Dudziramutauro_reChishona.txt"

def load_checkpoint():
    if os.path.exists(CHECKPOINT_PATH):
        try:
            with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load checkpoint file: {e}. Starting fresh.")
    return {"pages": {}}

def save_checkpoint(data):
    try:
        with open(CHECKPOINT_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save checkpoint: {e}")

def main():
    if not os.path.exists(PDF_PATH):
        print(f"Error: PDF file not found at {PDF_PATH}")
        sys.exit(1)

    print(f"Opening PDF: {PDF_PATH}")
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    print(f"Total pages in PDF: {total_pages}")

    # Load checkpoint data
    checkpoint = load_checkpoint()
    pages_done = checkpoint.get("pages", {})
    
    print(f"Loaded checkpoint. Already completed pages: {len(pages_done)}/{total_pages}")

    # Initialize EasyOCR reader
    # Shona uses Latin alphabet, so English 'en' model works perfectly.
    print("Initializing EasyOCR reader (CPU mode)...")
    reader = easyocr.Reader(['en'], gpu=False)
    print("EasyOCR reader is ready!")

    for page_idx in range(total_pages):
        page_num_str = str(page_idx + 1)
        
        if page_num_str in pages_done:
            print(f"Page {page_num_str}/{total_pages} already processed (skipped).")
            continue

        print(f"Processing Page {page_num_str}/{total_pages}...")
        
        try:
            # 1. Render PDF page to an image
            page = doc.load_page(page_idx)
            # Increase zoom to get higher resolution image for better OCR accuracy
            # A zoom factor of 2.0 scales the resolution by 2x (e.g. 150-300 DPI)
            zoom = 2.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # 2. Load the pixmap data as PIL Image or convert directly to bytes
            img_bytes = pix.tobytes("png")
            
            # 3. Perform OCR
            # easyocr can take image bytes directly as input
            ocr_results = reader.readtext(img_bytes)
            
            # 4. Extract and combine the text lines
            # ocr_results format is: [([[x1, y1], ...], "text", confidence), ...]
            # Sort the lines by their top-left vertical coordinate first, then horizontal coordinate
            # (EasyOCR usually returns them in a sensible reading order, but joining them with space/newline works)
            page_text_lines = []
            for bbox, text, conf in ocr_results:
                page_text_lines.append(text)
                
            page_text = "\n".join(page_text_lines)
            
            # Print a quick preview of the extracted text
            preview = page_text[:120].replace('\n', ' ')
            print(f"  OCR Result Preview: {preview}...")
            
            # 5. Save to checkpoint
            pages_done[page_num_str] = page_text
            checkpoint["pages"] = pages_done
            save_checkpoint(checkpoint)
            
        except Exception as e:
            print(f"Error processing Page {page_num_str}: {e}")
            # Save checkpoint even if it fails, to preserve whatever was done before
            save_checkpoint(checkpoint)
            sys.exit(1)

    print("\nAll pages processed successfully! Compiling final txt file...")
    
    # Compile the final text file in page order
    with open(OUTPUT_TXT_PATH, 'w', encoding='utf-8') as f_out:
        for p_idx in range(total_pages):
            p_num_str = str(p_idx + 1)
            f_out.write(f"--- PAGE {p_num_str} ---\n\n")
            f_out.write(pages_done.get(p_num_str, ""))
            f_out.write("\n\n")
            
    print(f"Success! Final text extracted and saved to: {OUTPUT_TXT_PATH}")
    
    # Optionally remove the checkpoint file now that we are done
    try:
        os.remove(CHECKPOINT_PATH)
        print("Cleaned up checkpoint file.")
    except Exception:
        pass

if __name__ == "__main__":
    main()
