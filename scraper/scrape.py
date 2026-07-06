import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import re
import sys
from pathlib import Path
import pypdf

# Setup absolute paths relative to script location
SCRIPT_DIR = Path(__file__).parent.resolve()
RAW_FOLDER = SCRIPT_DIR / ".." / "raw"
PDF_FOLDER = SCRIPT_DIR / ".." / "raw" / "downloads"

os.makedirs(RAW_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

BASE_URL = "https://dbgisre.edu.in/"
visited = set()

def clean_filename(url):
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if not path:
        return "homepage"
    filename = path.replace("/", "_")
    filename = re.sub(r'[^a-zA-Z0-9_]', '', filename)
    return filename

def extract_pdf_text(pdf_path):
    try:
        reader = pypdf.PdfReader(pdf_path)
        text_parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
        return "\n".join(text_parts)
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""

def guess_date_from_text_or_url(text, url):
    # Try url pattern /uploads/YYYY/MM/
    match = re.search(r'/uploads/(\d{4})/(\d{2})/', url)
    if match:
        year, month = match.groups()
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        try:
            month_name = months[int(month) - 1]
            return f"{month_name} 1, {year}"
        except:
            pass
        
    # Try searching text for date patterns, e.g. DD-MM-YYYY or DD/MM/YYYY
    match = re.search(r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b', text)
    if match:
        d, m, y = match.groups()
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        try:
            month_name = months[int(m) - 1]
            return f"{month_name} {d}, {y}"
        except:
            pass
            
    return "June 30, 2026"

def download_and_process_pdf(pdf_url):
    if pdf_url in visited:
        return
    visited.add(pdf_url)
    
    try:
        print(f"Downloading PDF: {pdf_url}")
        res = requests.get(pdf_url, timeout=15)
        if res.status_code == 200:
            name = clean_filename(pdf_url)
            pdf_path = os.path.join(PDF_FOLDER, f"{name}.pdf")
            with open(pdf_path, "wb") as f:
                f.write(res.content)
            
            text = extract_pdf_text(pdf_path)
            if text.strip():
                txt_name = f"noticeboard_pdf_{name}.txt"
                txt_path = os.path.join(RAW_FOLDER, txt_name)
                
                title = pdf_url.split("/")[-1].replace(".pdf", "").replace("-", " ").replace("_", " ").title()
                date_str = guess_date_from_text_or_url(text, pdf_url)
                
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(f"URL: {pdf_url}\n\n")
                    f.write(f"{title}\n")
                    f.write(f"{date_str}\n\n")
                    f.write(text)
                print(f"  [OK] Extracted PDF to: {txt_name}")
    except Exception as e:
        print(f"  [ERROR] Downloading/processing PDF {pdf_url}: {e}")

def scrape_page(url):
    if url in visited:
        return
    if len(visited) >= 20:
        print("Reached maximum page limit (20). Stopping crawl.")
        return
    visited.add(url)
    
    # Restrict crawling to main domains only to avoid external scraping loops
    if BASE_URL not in url:
        return

    try:
        print(f"Scraping HTML: {url}")
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "lxml")

        # Decompose layout tags
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        filename = clean_filename(url)
        filepath = os.path.join(RAW_FOLDER, f"{filename}.txt")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"URL: {url}\n\n")
            f.write(clean_text)

        print(f"  [OK] Saved HTML: {filename}.txt")

        # Crawl page links
        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(BASE_URL, href)

            if BASE_URL in full_url:
                if full_url.endswith(".pdf"):
                    download_and_process_pdf(full_url)
                elif not full_url.endswith((".jpg", ".png", ".jpeg", ".doc", ".docx", ".webp")):
                    scrape_page(full_url)

    except Exception as e:
        print(f"  [ERROR] Scraping {url}: {e}")

if __name__ == "__main__":
    scrape_page(BASE_URL)
    print("Scraping completed!")
