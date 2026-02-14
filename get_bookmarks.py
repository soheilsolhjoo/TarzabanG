"""
INSTRUCTIONS FOR USE:
---------------------
This utility script lists all bookmarks (Table of Contents) found in the PDF.
It is useful for identifying the 'index' numbers and page ranges for each section.

How to run:
./venv/bin/python get_bookmarks.py

Outcome:
Prints a hierarchical list of bookmark titles and their corresponding page numbers.
Use the order in this list to determine which --index to use with main.py.
"""

import fitz # PyMuPDF

def list_bookmarks(pdf_path):
    """
    Opens the PDF and prints its Table of Contents.
    """
    # Open the document
    doc = fitz.open(pdf_path)
    
    # Retrieve the Table of Contents (TOC)
    # toc entries are: [level, title, page]
    toc = doc.get_toc()
    
    if not toc:
        print("No bookmarks found in this PDF.")
        return
    
    print(f"Bookmarks found in {pdf_path}:")
    for level, title, page in toc:
        # Create indentation based on the bookmark level (hierarchy)
        indent = "  " * (level - 1)
        print(f"{indent}- {title} (Page {page})")
    
    doc.close()

if __name__ == "__main__":
    # Specify the file to analyze
    list_bookmarks("Politics.pdf")