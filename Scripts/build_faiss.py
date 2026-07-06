import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

with open("../output/dbgi_structured.json", "r", encoding="utf-8") as f:
    data = json.load(f)

model = SentenceTransformer("all-MiniLM-L6-v2")

texts = [item["text"] for item in data]

embeddings = model.encode(texts)

embeddings = np.array(embeddings).astype("float32")

dimension = embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)

index.add(embeddings)

faiss.write_index(
    index,
    "../vector_db/dbgi_index.faiss"
)

print("Vectors stored:", index.ntotal)