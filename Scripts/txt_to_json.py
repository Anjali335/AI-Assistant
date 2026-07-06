import json
from pathlib import Path

PROCESSED_FOLDER = Path("../processed")

files = list(PROCESSED_FOLDER.glob("*.txt"))

data = []

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()

    data.append({
        "filename": file.name,
        "content": content
    })

with open("../output/dbgi_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Saved {len(data)} records")