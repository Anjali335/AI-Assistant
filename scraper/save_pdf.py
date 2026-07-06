from reportlab.platypus import SimpleDocTemplate, Preformatted
from reportlab.lib.styles import getSampleStyleSheet
import os

input_folder = "../data/raw"
output_folder = "../data/pdfs"

os.makedirs(output_folder, exist_ok=True)

styles = getSampleStyleSheet()

for file in os.listdir(input_folder):

    if file.endswith(".txt"):

        path = os.path.join(input_folder, file)

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Remove problematic symbols
        content = content.replace("<", "")
        content = content.replace(">", "")

        pdf_name = file.replace(".txt", ".pdf")

        pdf_path = os.path.join(output_folder, pdf_name)

        doc = SimpleDocTemplate(pdf_path)

        story = []

        pre = Preformatted(
            content,
            styles["Code"]
        )

        story.append(pre)

        doc.build(story)

        print(f"PDF Created: {pdf_name}")

print("All PDFs generated successfully!")