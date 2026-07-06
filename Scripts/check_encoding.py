import json

with open("../output/notice_dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)

bad = []

for record in data:
    text = record["title"]

    if "â" in text or "�" in text:
        bad.append(text)

print("Bad records:", len(bad))

for item in bad[:20]:
    print(item)