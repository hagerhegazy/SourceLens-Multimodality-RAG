import os, fitz
import config

def chunk_words(text, size=config.CHUNK_WORDS, overlap=config.CHUNK_OVERLAP):
    words = text.split()
    step = size - overlap
    return [" ".join(words[i:i + size]) for i in range(0, max(len(words), 1), step) if words[i:i + size]]

def ingest_pdf(path):
    name = os.path.basename(path)
    records = []
    for page_no, page in enumerate(fitz.open(path), start=1):
        for i, chunk in enumerate(chunk_words(page.get_text())):
            records.append({
                "id": f"{name}-p{page_no}-c{i}",
                "modality": "text",
                "content": chunk,
                "source": name,
                "location": page_no,
                "thumb": "",
            })
    return records
