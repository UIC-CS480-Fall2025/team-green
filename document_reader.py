import pdfminer # pip install pdfminer.six
import os
import glob
import re

from pdfminer.high_level import extract_text
# import logging # to suppress color gradient warnings from pdfminer.six since we only care about reading text
# logging.getLogger("pdfminer").setLevel(logging.WARNING) # suppressing warnings only

CORPUS = "Corpus"
PROCESSED = "Processed_pdf"
CHUNKED = "Chunked_txt"

# Use regex to find repetitive whitespace and replace it with a singular space.
def normalize(s: str) -> str:
    """Collapse whitespace and trim."""
    return re.sub(r"\s+", " ", s).strip()

# Chunks the contents of 'text'
def chunk_text(text: str, max_words: int, overlap: int):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i+max_words]
        if not chunk:
            break
        chunks.append(" ".join(chunk))
        i += max_words - overlap # slides window
    return chunks

# Process Corpus pdf files into text files
def process_pdf_to_txt():
    project_root = os.path.abspath(os.path.dirname(__file__))  # Repo root
    data_corpus = os.path.join(project_root, CORPUS) # Input directory
    data_output = os.path.join(project_root, PROCESSED) # Output directory
    pdf_files = glob.glob(os.path.join(data_corpus, "*.pdf"))

    for pdf_path in pdf_files:
        output_path = data_output + "\\" + os.path.basename(pdf_path).rstrip(".pdf") + ".txt"

        if not os.path.exists(output_path):
            try:
                text = extract_text(pdf_path)
                with open(output_path, "x", encoding="utf-8") as f:
                    f.write(text)
                    f.close()
            except Exception as e:
                print(f"Failed to process {pdf_path}: {e}")

# Chunk processed text files into new text files with one chunking per line
def chunk_processed_txt():
    project_root = os.path.abspath(os.path.dirname(__file__))  # Repo root
    data_processed = os.path.join(project_root, PROCESSED) # Input directory
    data_output = os.path.join(project_root, CHUNKED) # Output directory
    txt_files = glob.glob(os.path.join(data_processed, "*.txt"))

    for txt_path in txt_files:
        output_path = data_output + "\\" + os.path.basename(txt_path)

        if not os.path.exists(output_path):
            with open(txt_path, "r", encoding="utf-8") as r:
                text = r.read()
                r.close()
            
            text = normalize(text) # strips repetitive whitespace
            chunked = chunk_text(text, 20, 10)

            with open(output_path, "x", encoding="utf-8") as f:
                for chunk in chunked:
                    f.write(chunk + "\n")
                f.close()

process_pdf_to_txt()
chunk_processed_txt()