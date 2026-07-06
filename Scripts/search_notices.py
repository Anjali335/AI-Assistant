import json
import faiss
from sentence_transformers import SentenceTransformer

with open("../output/notice_dataset.json", "r", encoding="utf-8") as f:
    notices = json.load(f)

model = SentenceTransformer("all-MiniLM-L6-v2")

index = faiss.read_index("../vector_db/notice_index.faiss")

query = input("Ask: ")

query_vector = model.encode([query])

D, I = index.search(query_vector, 5)

print("\nTop Results:\n")

for idx in I[0]:
    notice = notices[idx]

    print("=" * 50)
    print("Date:", notice["date"])
    print("Title:", notice["title"])
    print("Category:", notice["category"])