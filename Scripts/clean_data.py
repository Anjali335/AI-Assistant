from pathlib import Path

RAW_FOLDER = Path("../raw")
PROCESSED_FOLDER = Path("../processed")

PROCESSED_FOLDER.mkdir(exist_ok=True)

files = list(RAW_FOLDER.glob("*.txt"))

for file in files:
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    content = content.replace("�", "")
    content = content.replace("0\n", "")

    output_file = PROCESSED_FOLDER / file.name

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

print(f"Processed {len(files)} files")