"""
INSTRUCTIONS FOR USE:
---------------------
This script extracts raw text from all PDF slices located in the 'sections/' folder.
It is intended to be used BEFORE refinement.

How to run:
./venv/bin/python extract_all.py

Outcome:
For every .pdf file in 'sections/', a corresponding .txt file will be created 
containing the raw text. You can then open these .txt files and manually refine 
the text (e.g., removing page numbers, headers, or formatting errors) before 
submitting them for translation with main.py.
"""

import fitz  # PyMuPDF
import os

SECTIONS_FOLDER = "sections"

def extract_all():
    """
    Iterates through all PDF files in the sections folder and extracts their text.
    """
    # Ensure the folder exists
    if not os.path.exists(SECTIONS_FOLDER):
        print("Sections folder not found. Please run main.py once to slice the PDF.")
        return

    # List and sort all PDF files to process them in order
    files = [f for f in os.listdir(SECTIONS_FOLDER) if f.endswith(".pdf")]
    files.sort()

    for filename in files:
        pdf_path = os.path.join(SECTIONS_FOLDER, filename)
        txt_path = pdf_path.replace(".pdf", ".txt")
        
        # Avoid overwriting existing text files to protect manual refinements
        if not os.path.exists(txt_path):
            print(f"Extracting: {filename}")
            try:
                # Open the PDF slice
                doc = fitz.open(pdf_path)
                # Concatenate text from all pages in this slice
                text = "\n".join([page.get_text() for page in doc])
                # Save as a text file
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text)
                doc.close()
            except Exception as e:
                print(f"Error extracting {filename}: {e}")
        else:
            print(f"Skipping (already exists): {os.path.basename(txt_path)}")

if __name__ == "__main__":
    extract_all()