import json
import os
import sys
from pathlib import Path
# import faiss
# import numpy as np
# from sentence_transformers import SentenceTransformer

# Fix encoding issues in Windows console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


# Setup absolute paths relative to script location to allow running from any CWD
SCRIPT_DIR = Path(__file__).parent.resolve()
dataset_path = SCRIPT_DIR / ".." / "output" / "notice_dataset.json"
index_path = SCRIPT_DIR / ".." / "vector_db" / "notice_index.faiss"

if not dataset_path.exists():
    print(f"Error: Notice dataset not found at: {dataset_path}")
    sys.exit(1)

with open(dataset_path, "r", encoding="utf-8") as f:
    data = json.load(f)

texts = []
for item in data:
    text = f"{item.get('title', '')} {item.get('category', '')} {item.get('content', '')}"
    texts.append(text)

print("Notices loaded for encoding:", len(texts))

if not texts:
    print("Warning: No text content found to embed!")
    sys.exit(0)

print("Loading sentence transformer model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

print("Encoding texts (this may take a few seconds)...")
embeddings = model.encode(texts, show_progress_bar=True)
embeddings = np.array(embeddings).astype("float32")

dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# Ensure target directory exists before writing index
index_path.parent.mkdir(parents=True, exist_ok=True)

print(f"Writing FAISS index to: {index_path}")
faiss.write_index(index, str(index_path))

print("Vectors stored successfully. Total:", index.ntotal)
