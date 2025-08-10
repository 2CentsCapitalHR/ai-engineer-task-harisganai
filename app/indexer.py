"""
Simple local indexer: loads PDFs/TXT from app/docs and indexes chunks into FAISS using sentence-transformers.
Run as: python -m app.indexer
"""
import os
from pathlib import Path
import pickle
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import faiss

BASE = Path(__file__).resolve().parent
DOCS_DIR = BASE / "docs"
INDEX_DIR = BASE / "indexes"
INDEX_DIR.mkdir(exist_ok=True)

MODEL_NAME = os.environ.get("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE = 500
OVERLAP = 100


def load_texts(folder: Path):
    texts = []
    for p in folder.glob("**/*"):
        if p.suffix.lower() in {".txt", ".md"}:
            texts.append((str(p), p.read_text(encoding='utf-8', errors='ignore')))
        elif p.suffix.lower() in {".pdf"}:
            # naive: try using pdftotext via poppler if present; otherwise skip
            try:
                import pdfplumber
                with pdfplumber.open(p) as pdf:
                    pages = [page.extract_text() or "" for page in pdf.pages]
                texts.append((str(p), "\n".join(pages)))
            except Exception:
                print(f"Skipping PDF (no parser): {p}")
    return texts


def chunk_text(text, size=CHUNK_SIZE, overlap=OVERLAP):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i+size])
        chunks.append(chunk)
        i += size - overlap
    return chunks


def build_index():
    model = SentenceTransformer(MODEL_NAME)
    docs = load_texts(DOCS_DIR)
    all_chunks = []
    meta = []
    for path, text in docs:
        chunks = chunk_text(text)
        for c in chunks:
            all_chunks.append(c)
            meta.append({"source": path})
    if not all_chunks:
        print("No docs to index in app/docs. Create the directory and add reference PDFs/txts.")
        return
    embeddings = model.encode(all_chunks, show_progress_bar=True, convert_to_numpy=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    # save
    faiss.write_index(index, str(INDEX_DIR / "adgm_index.faiss"))
    with open(INDEX_DIR / "meta.pkl", "wb") as f:
        pickle.dump(meta, f)
    print("Index built with", len(all_chunks), "chunks")


if __name__ == "__main__":
    build_index()