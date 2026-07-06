from pathlib import Path

file = Path("../processed/2025_07.txt")

with open(file, "r", encoding="utf-8") as f:
    content = f.read()

lines = content.split("\n")

for i, line in enumerate(lines[:80]):
    print(i, "=>", repr(line))