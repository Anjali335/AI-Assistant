import re
import json
from pathlib import Path

PROCESSED_FOLDER = Path("../processed")

date_pattern = re.compile(r'^[A-Z][a-z]+ \d{1,2}, \d{4}$')

categories_map = {
    "news": "News",
    "placements": "Placements",
    "noticeboard": "Notice Board",
    "aktu": "AKTU",
    "bteup": "BTEUP",
    "msu": "MSU",
    "uncategorized": "Uncategorized"
}

# Standard WordPress footer/boilerplate items to filter out
boilerplate_keywords = [
    "leave a reply",
    "cancel reply",
    "your email address will not be published",
    "required fields are marked",
    "comment",
    "name",
    "email",
    "website",
    "save my name, email",
    "sitemanager",
    "0",
    "leave a comment",
    "post comment"
]

def is_boilerplate(line):
    line_lower = line.strip().lower()
    if not line_lower:
        return True
    # Match exact boilerplate fields or prefixes
    for kw in boilerplate_keywords:
        if line_lower == kw or line_lower.startswith(kw + "*") or line_lower.startswith(kw + " *") or line_lower.startswith("your email"):
            return True
    return False

all_records = []

# --- Step 1: Parse all files in processed folder ---
for file in PROCESSED_FOLDER.glob("*.txt"):
    filename = file.name.lower()
    
    with open(file, "r", encoding="utf-8") as f:
        content_text = f.read()
    
    # Normalize spaces
    content_text = content_text.replace('\xa0', ' ')
    lines = [line.strip() for line in content_text.split('\n')]
    
    # Check if this is a specific post file
    # Specific post files are prefixed with categories (noticeboard_, placements_, news_, etc.)
    is_specific_post = False
    file_category = "Notice Board"
    
    for prefix, cat in categories_map.items():
        if filename.startswith(prefix + "_"):
            is_specific_post = True
            file_category = cat
            break
            
    # Extract URL if available
    url = ""
    if lines and lines[0].startswith("URL:"):
        url = lines[0].replace("URL:", "").strip()
        
    if is_specific_post:
        # Specific post files have a Title around line 3 (index 2) and Date around line 4 (index 3)
        # E.g.:
        # Line 1: URL: ...
        # Line 2: (empty)
        # Line 3: Title - DBGI SAHARANPUR
        # Line 4: Date
        title = ""
        date = ""
        content_lines = []
        
        # Look for Title and Date
        for idx in range(1, min(10, len(lines))):
            line = lines[idx]
            if date_pattern.match(line):
                date = line
                # Title is usually the line before
                if idx - 1 >= 0 and lines[idx - 1] and not lines[idx - 1].startswith("URL:"):
                    title = lines[idx - 1]
                elif idx - 2 >= 0 and lines[idx - 2] and not lines[idx - 2].startswith("URL:"):
                    title = lines[idx - 2]
                
                # Content starts after the date
                content_start_idx = idx + 1
                for c_line in lines[content_start_idx:]:
                    if is_boilerplate(c_line):
                        continue
                    content_lines.append(c_line)
                break
        
        # Clean title
        if title:
            title = re.sub(r'\s*–\s*DBGI SAHARANPUR.*$', '', title, flags=re.IGNORECASE).strip()
            title = re.sub(r'\s*–\s*Top Engineering.*$', '', title, flags=re.IGNORECASE).strip()
        
        # If we failed to find a date, check if first line of content is a title
        if not title and len(lines) > 2:
            title = lines[2]
            content_lines = [l for l in lines[3:] if not is_boilerplate(l)]
            
        full_content = "\n".join(content_lines).strip()
        
        if title:
            all_records.append({
                "source_file": file.name,
                "url": url,
                "date": date or "Static Info",
                "title": title,
                "content": full_content,
                "category": file_category
            })
            
    else:
        # This is an archive page (like 2025_08.txt), category page, or homepage
        # We parse dated lists of notices
        i = 0
        while i < len(lines):
            if date_pattern.match(lines[i]):
                date = lines[i]
                title = lines[i + 1] if i + 1 < len(lines) else ""
                
                content = ""
                category = "Notice Board"
                
                # Check if next lines have category or content
                if i + 2 < len(lines):
                    potential_cat = lines[i + 2]
                    # Check if it matches a category
                    matched_cat = None
                    for cat_val in categories_map.values():
                        if potential_cat.lower() == cat_val.lower() or potential_cat.lower() == "notice board":
                            matched_cat = cat_val
                            break
                    
                    if matched_cat:
                        category = matched_cat
                    else:
                        content = potential_cat
                        if i + 3 < len(lines):
                            potential_cat2 = lines[i + 3]
                            for cat_val in categories_map.values():
                                if potential_cat2.lower() == cat_val.lower() or potential_cat2.lower() == "notice board":
                                    category = cat_val
                                    break
                
                # Clean title
                title = re.sub(r'\s*–\s*DBGI SAHARANPUR.*$', '', title, flags=re.IGNORECASE).strip()
                title = re.sub(r'\s*–\s*Top Engineering.*$', '', title, flags=re.IGNORECASE).strip()
                
                if title:
                    all_records.append({
                        "source_file": file.name,
                        "url": url,
                        "date": date,
                        "title": title,
                        "content": content.strip(),
                        "category": category
                    })
            i += 1

# --- Step 2: Add General static sections from homepage.txt and other files ---
# We chunk specific static sections of interest
homepage_path = PROCESSED_FOLDER / "homepage.txt"
if homepage_path.exists():
    with open(homepage_path, "r", encoding="utf-8") as f:
        hp_text = f.read().replace('\xa0', ' ')
    
    # 1. DBGI Saharanpur Intro Paragraph
    intro_match = re.search(r'Dev Bhoomi Group Of Institutions\(DBGI\) Saharanpur campus established.*?\.', hp_text, re.DOTALL)
    if intro_match:
        # Grab the full description paragraph
        intro_para_match = re.search(r'(Dev Bhoomi Group Of Institutions\(DBGI\) Saharanpur campus established.*?National Forest\.)', hp_text, re.DOTALL)
        if intro_para_match:
            all_records.append({
                "source_file": "homepage.txt",
                "url": "https://dbgisre.edu.in/",
                "date": "Static Info",
                "title": "About DBGI Saharanpur Campus & History",
                "content": intro_para_match.group(1).strip(),
                "category": "General Info"
            })

    # 2. Courses Offered Section
    courses_match = re.search(r'Courses We Are Offering.*?(Diploma In Mechanical Engineering\(Production\))', hp_text, re.DOTALL)
    if courses_match:
        courses_text = (
            "DBGI Saharanpur offers a wide range of professional courses in Engineering, Management, "
            "Computer Applications, Pharmacy, and Polytechnic. Featured programs include:\n"
            "- Diploma in Pharmacy (D.Pharm)\n"
            "- Diploma in Electrical Engineering\n"
            "- Diploma in Computer Science & Engineering (CSE)\n"
            "- Diploma in Mechanical Engineering (Production)"
        )
        all_records.append({
            "source_file": "homepage.txt",
            "url": "https://dbgisre.edu.in/",
            "date": "Static Info",
            "title": "Courses Offered at DBGI Saharanpur",
            "content": courses_text,
            "category": "General Info"
        })

    # 3. Training Program
    training_match = re.search(r'TRANING PROGRAM 2026.*?(?=Student Space|About Dev Bhoomi Group|$)', hp_text, re.DOTALL)
    if training_match:
        all_records.append({
            "source_file": "homepage.txt",
            "url": "https://dbgisre.edu.in/",
            "date": "Static Info",
            "title": "DBGI Training Program 2026",
            "content": "DBGI runs a comprehensive training program to help students acquire real-world skills for success and launch their careers with confidence. The program focuses on practical coding, system design, business administration, and placement preparation.",
            "category": "General Info"
        })

    # 4. TVARAN Annual Fest
    tvaran_match = re.search(r'TVARAN.*?(Vibrant annual.*?performances)', hp_text, re.DOTALL)
    if tvaran_match:
        all_records.append({
            "source_file": "homepage.txt",
            "url": "https://dbgisre.edu.in/",
            "date": "Static Info",
            "title": "TVARAN - Annual Cultural & Technical Fest",
            "content": "TVARAN is a vibrant annual, student-organized festival at DBGI Saharanpur featuring cultural competitions, technical symposiums, sports events, and celebrity star performances.",
            "category": "General Info"
        })

    # 5. Parse admission.txt for Admission, Fees, Contact and Courses
    admission_path = PROCESSED_FOLDER / "admission.txt"
    if admission_path.exists():
        with open(admission_path, "r", encoding="utf-8") as f:
            adm_text = f.read().replace('\xa0', ' ')

        # Entry 1: Fee Structure
        all_records.append({
            "source_file": "admission.txt",
            "url": "https://www.dbgisre.edu.in/fee-structure/",
            "date": "Static Info",
            "title": "DBGI Saharanpur Annual Fee Structure 2025-26",
            "category": "Admission",
            "content": (
                "Annual Fee Structure for the Academic Session 2025-26:\n"
                "- **B. Tech**: ₹ 55,000/-\n"
                "- **B. Pharma**: ₹ 63,300/-\n"
                "- **MBA**: ₹ 59,700/-\n"
                "- **MCA**: ₹ 55,000/-\n"
                "- **Polytechnic (Diploma Engg)**: ₹ 30,150/-\n"
                "- **D. Pharma**: ₹ 45,000/-\n"
                "- **BBA**: ₹ 24,500/-\n"
                "- **BCA**: ₹ 35,500/-\n"
                "- **B.COM**: ₹ 10,455/-\n\n"
                "Official Fee Structure page: https://www.dbgisre.edu.in/fee-structure/"
            )
        })

        # Entry 2: Contact Info
        all_records.append({
            "source_file": "admission.txt",
            "url": "https://dbgisre.edu.in/contact-us/",
            "date": "Static Info",
            "title": "DBGI Saharanpur Admissions Office and Contact Information",
            "category": "General Info",
            "content": (
                "DBGI Saharanpur Admissions Office Address & Contact details:\n"
                "- **Address**: OUR ADMISSIONS OFFICE, 7 Km. Milestone Dabki Road, Village Beri Jamapur Ahtemal Via Civil Hospital Xing, Saharanpur (Uttar Pradesh) 247001\n"
                "- **Email**: dbgi@dbgisre.edu.in\n"
                "- **Contact Numbers**: +91 9568775222, +91 9568776222\n\n"
                "Official Social Media Links:\n"
                "- **Facebook**: https://www.facebook.com/dbgisre\n"
                "- **Instagram**: https://www.instagram.com/dbgi.saharanpur/\n"
                "- **YouTube**: https://www.youtube.com/@dbgisaharanpurofficial\n"
                "- **Google Maps Location**: https://maps.google.com/?q=Dev+Bhoomi+Group+of+Institutions+Saharanpur"
            )
        })

        # Entry 3: Academic Calendars, Syllabus & Results Portals
        all_records.append({
            "source_file": "admission.txt",
            "url": "https://dbgisre.edu.in/result/",
            "date": "Static Info",
            "title": "DBGI Academic Portals, Syllabus, Results & Calendars",
            "category": "General Info",
            "content": (
                "Official links and portals for DBGI students:\n"
                "- **Previous Year Exam Papers**: https://dbgisre.edu.in/old-exam-papers/\n"
                "- **Syllabus details**: DBGI page (https://dbgisre.edu.in/syllabus/), AKTU (https://aktu.ac.in/syllabus.html), MSU (https://msuniversity.ac.in/syllabus.php), BTE UP (https://bteup.ac.in/webapp/home.aspx)\n"
                "- **Academic Calendar**: DBGI page (https://dbgisre.edu.in/academic-calender/), AKTU (https://aktu.ac.in/academic-calender.html), MSU (https://msuniversity.ac.in/academic-calender.php), BTE UP (https://bteup.ac.in/webapp/home.aspx)\n"
                "- **Result Portals**: DBGI page (https://dbgisre.edu.in/result/), AKTU OneView (https://erp.aktu.ac.in/WebPages/OneView/OneView.aspx), MSU Results (https://msuresults.com/), BTE UP Portal (https://bteup.ac.in/webapp/home.aspx)"
            )
        })

        # Entry 4: Courses and Application Links
        all_records.append({
            "source_file": "admission.txt",
            "url": "https://dbgisre.edu.in/student-registration/",
            "date": "Static Info",
            "title": "DBGI Saharanpur Courses Offered & Admission Links",
            "category": "Admission",
            "content": (
                "Complete directory of courses and programs offered at DBGI Saharanpur:\n"
                "- **B.Tech - Computer Science & Engineering**: https://www.dbgisre.edu.in/b-tech-computer-science-engineering/\n"
                "- **B.Tech - Civil Engineering**: https://www.dbgisre.edu.in/b-tech-civil-engineering/\n"
                "- **B.Tech - Electrical & Electronics Engineering**: https://www.dbgisre.edu.in/b-tech-electrical-electronics-engineering/\n"
                "- **B.Tech - Mechanical Engineering (ME)**: https://www.dbgisre.edu.in/b-tech-mechanical-engineering-me/\n"
                "- **B.Tech - Electronics & Communication Engineering**: https://www.dbgisre.edu.in/b-tech-electronics-and-communication-engineering/\n"
                "- **MBA (Master of Business Administration)**: https://www.dbgisre.edu.in/master-of-business-administration-mba\n"
                "- **MCA (Master of Computer Application)**: https://www.dbgisre.edu.in/master-of-computer-application-mca\n"
                "- **BCA (Bachelor of Computer Application)**: https://www.dbgisre.edu.in/bachelor-of-computer-application-bca\n"
                "- **BBA (Bachelor of Business Administration)**: https://www.dbgisre.edu.in/bachelor-of-business-administration-bba\n"
                "- **B.Pharm (Bachelor of Pharmacy)**: https://www.dbgisre.edu.in/bachelor-of-pharmacy-b-pharma\n"
                "- **D.Pharm (Diploma in Pharmacy)**: https://www.dbgisre.edu.in/diploma-in-pharmacy\n"
                "- **Diploma in Civil Engineering**: https://www.dbgisre.edu.in/diploma-in-civil-engineering/\n"
                "- **Diploma in Computer Science & Engineering**: https://www.dbgisre.edu.in/diploma-in-computer-science-engg/\n"
                "- **Diploma in Mechanical Engineering (Automobile)**: https://www.dbgisre.edu.in/diploma-in-mechanical-engineeringautomobile/\n"
                "- **Diploma in Mechanical Engineering (Production)**: https://www.dbgisre.edu.in/diploma-in-mechanical-engineeringproduction/\n"
                "- **Diploma in Electrical Engineering**: https://www.dbgisre.edu.in/diploma-in-electrical-engineering/\n"
                "- **Diploma in Electronics & Communication**: https://www.dbgisre.edu.in/diploma-in-electronics-communication/\n\n"
                "Apply or Register for Admission here: https://dbgisre.edu.in/student-registration/"
            )
        })

# --- Step 3: De-duplicate records by title ---
# If a notice exists both in list and as specific post, we keep the one with longer content.
unique_records = {}
for rec in all_records:
    title_key = rec["title"].lower().strip()
    # Normalize title_key (remove extra spaces and punctuation)
    title_key = re.sub(r'[^\w\s]', '', title_key)
    title_key = " ".join(title_key.split())
    
    if not title_key:
        continue
        
    if title_key not in unique_records:
        unique_records[title_key] = rec
    else:
        # Keep the one with longer content length
        existing_len = len(unique_records[title_key].get("content", ""))
        new_len = len(rec.get("content", ""))
        if new_len > existing_len:
            unique_records[title_key] = rec
        elif new_len == existing_len and rec.get("url") and not unique_records[title_key].get("url"):
            # Prefer the one with URL
            unique_records[title_key] = rec

final_records = list(unique_records.values())

# Sort final records: notices with dates first, sorted by title
final_records.sort(key=lambda x: (x.get("date") == "Static Info", x.get("title", "")))

# Write output
output_path = Path("../output/notice_dataset.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(final_records, f, indent=2, ensure_ascii=False)

print(f"Generated unified notice_dataset.json with {len(final_records)} unique records!")