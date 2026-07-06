import json
import faiss
from sentence_transformers import SentenceTransformer

with open("../output/notice_dataset.json", "r", encoding="utf-8") as f:
    notices = json.load(f)

model = SentenceTransformer("all-MiniLM-L6-v2")

index = faiss.read_index("../vector_db/notice_index.faiss")

while True:

    query = input("\nAsk DBGI Assistant: ")

    if query.lower() == "exit":
        break

    query_vector = model.encode([query])

    D, I = index.search(query_vector, 5)

    print("\nRelevant Notices:\n")

    for rank, idx in enumerate(I[0], start=1):

        notice = notices[idx]

        print(f"{rank}. {notice['title']}")
        print(f"   Date: {notice['date']}")
        print(f"   Category: {notice['category']}")
        print()