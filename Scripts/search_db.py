import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Load data
with open("../output/dbgi_structured.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load FAISS index
index = faiss.read_index("../vector_db/dbgi_index.faiss")

# Query
query = input("Ask a question: ")

query_embedding = model.encode([query])
query_embedding = np.array(query_embedding).astype("float32")

# Search
distances, indices = index.search(query_embedding, 5)

print("\nTop Results:\n")

for idx in indices[0]:
    print("=" * 50)
    print(data[idx]["source_file"])
    print(data[idx]["text"][:500])
    print()