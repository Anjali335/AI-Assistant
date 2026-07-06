import json
from pathlib import Path

PROCESSED_FOLDER = Path("../processed")

records = []

for file in PROCESSED_FOLDER.glob("*.txt"):
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()

    records.append({
        "source_file": file.name,
        "text": content
    })

with open("../output/dbgi_structured.json", "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2, ensure_ascii=False)

print(f"Created {len(records)} records")