import re
from pathlib import Path

file = Path("../processed/2025_07.txt")

with open(file, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f.readlines()]

date_pattern = re.compile(r'^[A-Z][a-z]+ \d{1,2}, \d{4}$')

records = []

i = 0

while i < len(lines):
    if date_pattern.match(lines[i]):
        record = {
            "date": lines[i],
            "title": lines[i + 1] if i + 1 < len(lines) else "",
            "category": lines[i + 2] if i + 2 < len(lines) else ""
        }

        records.append(record)

    i += 1

print("Records found:", len(records))

for r in records[:5]:
    print(r)