import json
from sentence_transformers import SentenceTransformer

with open("../output/dbgi_structured.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("Records loaded:", len(data))

model = SentenceTransformer("all-MiniLM-L6-v2")

sample = data[0]["text"]

embedding = model.encode(sample)

print("Embedding dimension:", len(embedding))