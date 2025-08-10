from pathlib import Path
import os
import pickle
import faiss
from sentence_transformers import SentenceTransformer

BASE = Path(__file__).resolve().parent
INDEX_DIR = BASE / "indexes"
MODEL_NAME = os.environ.get("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

class LocalRetriever:
    def __init__(self):
        idx_file = INDEX_DIR / "adgm_index.faiss"
        meta_file = INDEX_DIR / "meta.pkl"
        if idx_file.exists() and meta_file.exists():
            self.index = faiss.read_index(str(idx_file))
            with open(meta_file, "rb") as f:
                self.meta = pickle.load(f)
            self.model = SentenceTransformer(MODEL_NAME)
        else:
            self.index = None
            self.meta = []
            self.model = SentenceTransformer(MODEL_NAME)

    def retrieve(self, query: str, top_k: int = 5):
        if self.index is None:
            return []
        q_emb = self.model.encode([query], convert_to_numpy=True)
        D, I = self.index.search(q_emb, top_k)
        results = []
        for idx in I[0]:
            if idx < 0 or idx >= len(self.meta):
                continue
            results.append(self.meta[idx])
        return results

if __name__ == "__main__":
    r = LocalRetriever()
    print(r.retrieve("jurisdiction adgm"))