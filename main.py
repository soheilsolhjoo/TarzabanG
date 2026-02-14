"""
TrazbanG
--------------------------
An interactive tool for high-fidelity document translation using Google Gemini.

CORE WORKFLOW:
1. SLICE:   Break a large PDF into manageable segments based on bookmarks or chapters.
2. EXTRACT: Pull raw text from those segments for manual cleanup.
3. REFINE:  (User Action) Edit the generated .txt files in the sections folder.
4. TRANSLATE: Submit the refined text or raw PDF segments to Gemini for translation.

FOLDER STRUCTURE:
- sections_<input_name>/: Created during 'slice' or 'extract'. Stores segment PDFs/TXTs.
- translations_<input_name>/: Created during 'translate'. Stores final translations.

COMMAND EXAMPLES:
- Prepare everything for a new book (slice + extract):
    python main.py --input Politics.pdf --action prepare
- Translate only a specific range after you've refined the text:
    python main.py --input Politics.pdf --action translate --start 5 --end 10
- Translate a single section:
    python main.py --input Book.pdf --action translate --index 3
- Full automation (not recommended for highest quality):
    python main.py --input Book.pdf --action all
"""

import os
import time
import logging
import re
import argparse
import fitz  # PyMuPDF
from google import genai

# --- DEFAULTS ---
DEFAULT_API_KEY = os.environ.get("GEMINI_API_KEY") # Recommended: Set this in your environment
DEFAULT_LANG = "Persian"
MODEL_NAME = "gemini-flash-latest"
GLOSSARY_PATH = "glossary.txt"
LOG_FILE = "translation_progress.log"

# Detailed instructions for the AI to ensure translation quality
STYLE_GUIDE = """
- Tone: Professional and serious.
- Structure: Keep sentence lengths as close to the original as possible.
- Constraint: Do not add, remove, or summarize sentences.
"""

def get_args():
    """Defines and parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Universal Gemini Translator")
    parser.add_argument("--input", required=True, help="Path to the source PDF or TXT file.")
    parser.add_argument("--mode", choices=['bookmark', 'chapter', 'full'], default='bookmark', 
                        help="Chunking strategy: 'bookmark' (TOC), 'chapter' (regex search), or 'full' (single chunk).")
    parser.add_argument("--action", choices=['slice', 'extract', 'translate', 'prepare', 'all'], default='all', 
                        help="Action to perform: slice (PDFs), extract (TXTs), translate (Gemini), prepare (slice+extract).")
    parser.add_argument("--lang", default=DEFAULT_LANG, help="Target language for translation.")
    parser.add_argument("--index", type=int, help="Limit action to a single section index.")
    parser.add_argument("--start", type=int, help="Start index for range processing.")
    parser.add_argument("--end", type=int, help="End index for range processing.")
    parser.add_argument("--key", default=DEFAULT_API_KEY, help="Google Gemini API Key.")
    return parser.parse_args()

def sanitize(text):
    """Sanitizes strings for safe cross-platform filenames."""
    return re.sub(r'[^\w\s-]', '', text).strip().replace(' ', '_')

def get_paths(input_path):
    """Generates unique folder names based on the input filename."""
    base = os.path.basename(input_path).rsplit('.', 1)[0]
    folder_name = sanitize(base)
    return f"sections_{folder_name}", f"translations_{folder_name}"

def is_in_range(idx, args):
    """Universal filter to check if a section should be processed."""
    if args.index is not None and idx != args.index: return False
    if args.start is not None and idx < args.start: return False
    if args.end is not None and idx > args.end: return False
    return True

def get_ranges(pdf_path, mode):
    """Determines the page ranges for each section based on the selected mode."""
    doc = fitz.open(pdf_path)
    ranges = []
    if mode == 'bookmark':
        toc = doc.get_toc()
        if not toc: 
            ranges = [{"index": 1, "title": "Full_Document", "start": 0, "end": len(doc)-1}]
        else:
            for i in range(len(toc)):
                level, title, start_page = toc[i]
                end_page = toc[i+1][2] - 1 if i + 1 < len(toc) else len(doc)
                ranges.append({"index": i + 1, "title": title, "start": start_page - 1, "end": end_page - 1})
    elif mode == 'chapter':
        chapters = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            if page.search_for("Chapter") or page.search_for("CHAPTER"):
                chapters.append(page_num)
        if not chapters: 
            ranges = [{"index": 1, "title": "Full_Document", "start": 0, "end": len(doc)-1}]
        else:
            unique_chapters = sorted(list(set(chapters)))
            for i in range(len(unique_chapters)):
                start = unique_chapters[i]
                end = unique_chapters[i+1] - 1 if i + 1 < len(unique_chapters) else len(doc) - 1
                ranges.append({"index": i + 1, "title": f"Chapter_{i+1}", "start": start, "end": end})
    else: # mode == 'full'
        ranges = [{"index": 1, "title": "Full_Document", "start": 0, "end": len(doc)-1}]
    doc.close()
    return ranges

def main():
    args = get_args()
    sec_folder, out_folder = get_paths(args.input)
    
    # Configure logging
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # Identify ranges if the input is a PDF
    ranges = get_ranges(args.input, args.mode) if args.input.lower().endswith('.pdf') else []

    # ACTION: SLICE (Splits PDF into smaller files)
    if args.action in ['slice', 'prepare', 'all']:
        if args.input.lower().endswith('.pdf'):
            if not os.path.exists(sec_folder): os.makedirs(sec_folder)
            doc = fitz.open(args.input)
            for item in ranges:
                if not is_in_range(item['index'], args): continue
                path = os.path.join(sec_folder, f"{item['index']:02d}_{sanitize(item['title'])}.pdf")
                if not os.path.exists(path):
                    print(f"Slicing index {item['index']}...")
                    new_doc = fitz.open()
                    new_doc.insert_pdf(doc, from_page=item['start'], to_page=item['end'])
                    new_doc.save(path)
                    new_doc.close()
            doc.close()
        else:
            print("Notice: Slicing skipped (only supported for PDF inputs).")

    # ACTION: EXTRACT (Extracts text from PDF slices for user refinement)
    if args.action in ['extract', 'prepare', 'all']:
        if os.path.exists(sec_folder):
            pdfs = sorted([f for f in os.listdir(sec_folder) if f.endswith('.pdf')])
            for pdf_name in pdfs:
                match = re.match(r'^(\d+)_', pdf_name)
                idx = int(match.group(1)) if match else 0
                if not is_in_range(idx, args): continue
                
                txt_path = os.path.join(sec_folder, pdf_name.replace('.pdf', '.txt'))
                if not os.path.exists(txt_path):
                    print(f"Extracting text for index {idx}...")
                    doc = fitz.open(os.path.join(sec_folder, pdf_name))
                    text = "\n".join([p.get_text() for p in doc])
                    with open(txt_path, 'w', encoding='utf-8') as f: f.write(text)
                    doc.close()
        elif not args.input.lower().endswith('.txt'):
            print(f"Folder {sec_folder} not found. Please run with '--action slice' first.")

    # ACTION: TRANSLATE (Sends content to Gemini API)
    if args.action in ['translate', 'all']:
        if not os.path.exists(out_folder): os.makedirs(out_folder)
        client = genai.Client(api_key=args.key)
        
        # Gather all processable files in the sections folder
        # For .txt inputs, it just looks in the current folder if necessary, but usually we use sections_ folder
        folder_to_scan = sec_folder if os.path.exists(sec_folder) else "."
        files = sorted([f for f in os.listdir(folder_to_scan) if f.endswith('.pdf') or f.endswith('.txt')])
        base_names = sorted(list(set([f.rsplit('.', 1)[0] for f in files])))

        for base in base_names:
            match = re.match(r'^(\d+)_', base)
            idx = int(match.group(1)) if match else 0
            if not is_in_range(idx, args): continue

            target_path = os.path.join(out_folder, f"{base}.txt")
            if os.path.exists(target_path): continue

            print(f"Translating index {idx} ({base})...")
            try:
                txt_path = os.path.join(folder_to_scan, f"{base}.txt")
                pdf_path = os.path.join(folder_to_scan, f"{base}.pdf")
                
                # Priority: 1. Refined Text, 2. Raw PDF Segment
                if os.path.exists(txt_path):
                    with open(txt_path, 'r', encoding='utf-8') as f: payload = f.read()
                elif os.path.exists(pdf_path):
                    payload = client.files.upload(file=pdf_path)
                    while payload.state == "PROCESSING":
                        time.sleep(2)
                        payload = client.files.get(name=payload.name)
                else: continue

                # Two-pass translation could be added here, currently single pass with prompt
                prompt = f"Translate the following to {args.lang}.\n\nSTYLE GUIDE:\n{STYLE_GUIDE}\n\nCONTENT:\n"
                response = client.models.generate_content(model=MODEL_NAME, contents=[payload, prompt])
                
                with open(target_path, 'w', encoding='utf-8') as f: f.write(response.text)
                logging.info(f"Successfully translated index {idx}: {base}")
                
            except Exception as e:
                print(f"Error on {base}: {e}")
                logging.error(f"Error on {base}: {e}")

    print("Task execution finished.")

if __name__ == "__main__":
    main()