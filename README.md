# TrazbanG

A high-fidelity document translation toolkit designed for large PDFs and text files. This tool supports a granular "Extract -> Refine -> Translate" workflow, ensuring the highest quality by enabling manual text cleanup before AI translation.

## Features
- **Smart Chunking**: Automatically slices PDFs based on Bookmarks (TOC) or Chapter headings.
- **Two-Pass Translation**: Performs a literal technical draft followed by an eloquent scholarly refinement.
- **Dual Outputs**: Saves both `_draft.txt` (literal) and `_final.txt` (eloquent) for every section.
- **Refinement-First Workflow**: Extracts raw text so you can fix OCR errors or remove headers/footers before translating.
- **Resumable**: Skips already processed segments to save time and API quota.
- **Flexible Filters**: Process a single section, a range of indices, or the entire book.
- **Systematic Organization**: Automatically creates dedicated folders for segments and translations based on the input filename.

## Installation
1. Ensure you have Python 3.10+ installed.
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install google-genai pymupdf
   ```
4. Set your Gemini API Key:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

## Usage

### 1. Preparation (Slicing & Extraction)
Break the PDF into manageable chunks and extract the text for refinement.
```bash
python main.py --input MyBook.pdf --mode bookmark --action prepare
```
- **Result**: A new folder `sections_MyBook/` is created containing `.pdf` segments and `.txt` extractions.

### 2. Manual Refinement (Recommended)
Open the `.txt` files in `sections_MyBook/` and clean up any "noise" like page numbers, running headers, or bad line breaks.

### 3. Translation
Submit your refined text to Gemini for a two-pass translation.
```bash
# Translate with a custom glossary (.json or .txt)
python main.py --input MyBook.pdf --action translate --glossary glossary.json

## Translate a single section
python main.py --input MyBook.pdf --action translate --index 7

# Translate a range of sections
python main.py --input MyBook.pdf --action translate --start 10 --end 20
```
- **Result**: Final translations are saved in `translations_MyBook/`.
    - `..._draft.txt`: The initial technical draft.
    - `..._final.txt`: The polished, natural translation.

**Note**: To re-translate a section, you must first remove or rename its existing `_final.txt` file.

## Command-Line Arguments

| Flag | Description | Options |
| :--- | :--- | :--- |
| `--input` | **(Required)** Path to your PDF or TXT file. | File path |
| `--mode` | How the book should be divided. | `bookmark` (default), `chapter`, `full` |
| `--action` | What step to perform. | `slice`, `extract`, `translate`, `prepare` (slice+extract) |
| `--lang` | The target language for translation. | e.g., `Persian`, `Spanish`, `French` |
| `--glossary`| Path to glossary file. | `.json` or `.txt` |
| `--index` | Process only this specific section number. | Integer |
| `--start` / `--end` | Process a range of sections. | Integers |
| `--key` | Your Google Gemini API Key. | String |

## Folders Created
- `sections_<filename>/`: Contains the sliced PDF parts and extracted text files.
- `translations_<filename>/`: Contains the final dual-pass output from Gemini.

## Acknowledgments
This project was entirely authored and architected by **Google Gemini**.
