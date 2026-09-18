import os
import re
import sys
import json
import urllib3
import requests
import pdfplumber
import pyarrow.parquet as pq
from bs4 import BeautifulSoup

# Disable insecure request warnings for SSL verification bypass
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NCERT_DIR = os.path.join(BASE_DIR, 'raw-textbooks', 'ncert')
CBSE_DIR = os.path.join(BASE_DIR, 'raw-textbooks', 'cbse')

os.makedirs(NCERT_DIR, exist_ok=True)
os.makedirs(CBSE_DIR, exist_ok=True)

# Subjects filter keywords
ALLOWED_KEYWORDS = [
    "english", "marigold", "raindrop", "blossoms", "science", "physics", 
    "chemistry", "biology", "environmental", "looking_around", "evs", 
    "mathematics", "math", "math_magic", "maths", "social_science", 
    "social_studies", "history", "geography", "economics", "civics", 
    "political", "computer_application", "information_technology"
]

EXCLUDED_KEYWORDS = [
    "hindi", "sanskrit", "urdu", "bengali", "marathi", "nepali", "assamese", 
    "telugu", "tamil", "manipuri", "gujarati", "kannada", "malayalam", "odia", 
    "punjabi", "tibetan", "arabic", "persian", "german", "french", "spanish", 
    "russian", "japanese", "bhutia", "bodo", "gurung", "kashmiri", "kokborok", 
    "lepcha", "limboo", "mizo", "sherpa", "tamang", "tangkhul", "thai", 
    "painting", "music", "carnatic", "hindustani", "home_science", "accountancy", 
    "business", "retail", "tourism", "marketing", "agriculture"
]

def cleanup_irrelevant_files():
    print("Starting cleanup of irrelevant subjects and non-English language files...")
    cleaned_count = 0
    
    for root, dirs, files in os.walk(BASE_DIR, topdown=False):
        # Skip the user-provided processed-pyq-pdfs folder entirely
        if "processed-pyq-pdfs" in root:
            continue
            
        for name in files:
            file_path = os.path.join(root, name)
            # Only clean up within raw-textbooks folder
            if "raw-textbooks" not in file_path:
                continue
                
            name_lower = name.lower()
            
            # Check exclusions
            is_excluded = any(ex in name_lower for ex in EXCLUDED_KEYWORDS)
            # Check inclusions
            is_included = any(inc in name_lower for inc in ALLOWED_KEYWORDS)
            
            # Keep raw parquet file
            if name == "0.parquet":
                continue
                
            if is_excluded or not is_included:
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                except Exception as e:
                    print(f"Error removing file {file_path}: {e}")
                    
        for name in dirs:
            dir_path = os.path.join(root, name)
            if "raw-textbooks" not in dir_path:
                continue
            if "processed-pyq-pdfs" in dir_path:
                continue
            
            # Remove empty directories
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    cleaned_count += 1
            except Exception:
                pass
                
    print(f"Cleanup completed. Removed {cleaned_count} irrelevant files/directories.")

def download_file(url, local_path):
    print(f"Downloading: {url} -> {local_path}")
    try:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=60)
        if r.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(r.content)
            print(f"Successfully downloaded {local_path} ({len(r.content)} bytes)")
            return True
        else:
            print(f"Failed to download {url}. Status code: {r.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def extract_pdf_text(pdf_path, txt_path):
    print(f"Extracting text: {pdf_path} -> {txt_path}")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text_pages = []
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    text_pages.append(f"--- PAGE {i+1} ---\n{text}")
            
            full_text = "\n\n".join(text_pages)
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
        print(f"Successfully extracted {txt_path} ({len(full_text)} characters)")
        return True
    except Exception as e:
        print(f"Error extracting PDF {pdf_path}: {e}")
        return False

def process_ncert_parquet(parquet_path):
    print(f"Reading NCERT parquet file: {parquet_path}")
    try:
        table = pq.read_table(parquet_path)
        data = table.to_pylist()
        print(f"Total rows in NCERT dataset: {len(data)}")
        
        # Group by grade and subject
        grouped = {}
        for row in data:
            grade = row.get('grade')
            subject = row.get('subject')
            if not grade or not subject:
                continue
                
            subject_lower = str(subject).lower()
            # Apply subject filters
            is_excluded = any(ex in subject_lower for ex in EXCLUDED_KEYWORDS)
            is_included = any(inc in subject_lower for inc in ALLOWED_KEYWORDS)
            if is_excluded or not is_included:
                continue
            
            key = (int(grade), str(subject).strip())
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(row)
            
        for (grade, subject), rows in grouped.items():
            class_dir = os.path.join(NCERT_DIR, f"class_{grade}")
            os.makedirs(class_dir, exist_ok=True)
            
            # Clean subject name for filename
            sub_clean = re.sub(r'[^a-zA-Z0-9_]', '_', subject).lower()
            
            # 1. Compile textbook summaries
            unique_topics = {}
            for r in rows:
                topic = r.get('Topic')
                explanation = r.get('Explanation')
                if topic and explanation:
                    unique_topics[topic.strip()] = explanation.strip()
            
            textbook_content = []
            for topic, explanation in sorted(unique_topics.items()):
                textbook_content.append(f"## Topic: {topic}\n\n{explanation}\n\n" + "="*50 + "\n")
            
            textbook_path = os.path.join(class_dir, f"{sub_clean}_textbook.txt")
            with open(textbook_path, 'w', encoding='utf-8') as f:
                f.write("\n\n".join(textbook_content))
                
            # 2. Compile Question Bank (JSONL)
            questions_path = os.path.join(class_dir, f"{sub_clean}_questions.jsonl")
            with open(questions_path, 'w', encoding='utf-8') as f:
                for r in rows:
                    q_data = {
                        "topic": r.get('Topic'),
                        "explanation": r.get('Explanation'),
                        "question": r.get('Question'),
                        "answer": r.get('Answer'),
                        "difficulty": r.get('Difficulty'),
                        "complexity": r.get('QuestionComplexity'),
                        "type": r.get('QuestionType')
                    }
                    f.write(json.dumps(q_data) + '\n')
            
            print(f"Processed Class {grade} {subject}: {len(unique_topics)} topics, {len(rows)} QA pairs.")
            
    except Exception as e:
        print(f"Error processing NCERT parquet: {e}")

def scrape_and_download_cbse_papers(year, class_val, url):
    print(f"Scraping CBSE Class {class_val} ({year}) from {url}")
    try:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=30)
        if r.status_code != 200:
            print(f"Failed to fetch page. Status: {r.status_code}")
            return
            
        soup = BeautifulSoup(r.text, 'html.parser')
        class_dir = os.path.join(CBSE_DIR, year, f"class_{class_val}")
        os.makedirs(class_dir, exist_ok=True)
        
        # Parse table rows
        rows = soup.find_all('tr')
        print(f"Found {len(rows)} table rows.")
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:
                continue
                
            subject_name = cells[0].text.strip()
            # Skip header rows
            if subject_name.lower() in ["subject", "s.no.", "s.no", ""]:
                continue
                
            subject_lower = subject_name.lower()
            # Filter subjects
            is_excluded = any(ex in subject_lower for ex in EXCLUDED_KEYWORDS)
            is_included = any(inc in subject_lower for inc in ALLOWED_KEYWORDS)
            if is_excluded or not is_included:
                continue
                
            # Find PDF links in the cells[1] (SQP) and cells[2] (MS)
            sqp_links = cells[1].find_all('a', href=re.compile(r'\.pdf$'))
            ms_links = cells[2].find_all('a', href=re.compile(r'\.pdf$'))
            
            sub_clean = re.sub(r'[^a-zA-Z0-9_]', '_', subject_name).lower()
            
            if sqp_links:
                href = sqp_links[0]['href']
                if not href.startswith('http'):
                    href = "https://cbseacademic.nic.in/" + href.lstrip('/')
                pdf_path = os.path.join(class_dir, f"{sub_clean}_sqp.pdf")
                txt_path = os.path.join(class_dir, f"{sub_clean}_sqp.txt")
                if download_file(href, pdf_path):
                    extract_pdf_text(pdf_path, txt_path)
                    
            if ms_links:
                href = ms_links[0]['href']
                if not href.startswith('http'):
                    href = "https://cbseacademic.nic.in/" + href.lstrip('/')
                pdf_path = os.path.join(class_dir, f"{sub_clean}_ms.pdf")
                txt_path = os.path.join(class_dir, f"{sub_clean}_ms.txt")
                if download_file(href, pdf_path):
                    extract_pdf_text(pdf_path, txt_path)
                    
    except Exception as e:
        print(f"Error scraping CBSE Class {class_val} ({year}): {e}")

def download_class_1_to_5():
    import urllib.parse
    # Mapping of grade and subject to archive.org details/URLs
    archive_mapping = {
        5: {
            "english": "ncert-eeen1",
            "evs": "ncert-eeap1",
            "mathematics": "class-ii-maths/Class V Maths.pdf"
        },
        4: {
            "english": "ncert-deen1",
            "evs": "ncert-deap1",
            "mathematics": "class-ii-maths/Class IV Maths.pdf"
        },
        3: {
            "english": "ncert-ceen1",
            "evs": "ncert-ceap1",
            "mathematics": "class-ii-maths/Class III Maths.pdf"
        },
        2: {
            "english": "ncert-been1",
            "mathematics": "class-ii-maths/Class II Maths.pdf"
        },
        1: {
            "english": "ncert-aeen1",
            "mathematics": "class-ii-maths/Class I Maths.pdf"
        }
    }
    
    print("Starting download of Class 1 to 5 textbooks from Internet Archive...")
    for grade, subjects in archive_mapping.items():
        grade_dir = os.path.join(NCERT_DIR, f"class_{grade}")
        os.makedirs(grade_dir, exist_ok=True)
        
        for subject, source in subjects.items():
            txt_path = os.path.join(grade_dir, f"{subject}_textbook.txt")
            if os.path.exists(txt_path):
                print(f"Class {grade} {subject} textbook already exists at {txt_path}. Skipping.")
                continue
                
            if "/" in source:
                # Direct single file download (e.g. class-ii-maths/Class V Maths.pdf)
                item_id, filename = source.split("/", 1)
                encoded_filename = urllib.parse.quote(filename)
                url = f"https://archive.org/download/{item_id}/{encoded_filename}"
                pdf_path = os.path.join(grade_dir, f"{subject}.pdf")

                txt_path = os.path.join(grade_dir, f"{subject}_textbook.txt")
                print(f"Downloading direct file: {url} -> {pdf_path}")
                if download_file(url, pdf_path):
                    if extract_pdf_text(pdf_path, txt_path):
                        print(f"Extracted and saved: {txt_path}")
                        try:
                            os.remove(pdf_path)
                        except Exception as e:
                            print(f"Error removing {pdf_path}: {e}")
            else:
                # Folder/Item-based download of chapters
                item_id = source
                print(f"Fetching Class {grade} {subject} from archive.org item: {item_id}")
                meta_url = f"https://archive.org/metadata/{item_id}"
                try:
                    r = requests.get(meta_url, timeout=30)
                    if r.status_code != 200:
                        print(f"Failed to fetch metadata for {item_id}. Status: {r.status_code}")
                        continue
                    
                    files = r.json().get('files', [])
                    pdf_files = [f['name'] for f in files if f['name'].endswith('.pdf')]
                    
                    chapter_pdfs = []
                    for fname in pdf_files:
                        if fname.startswith('.') or '_archive' in fname or 'meta' in fname:
                            continue
                        chapter_pdfs.append(fname)
                    
                    chapter_pdfs.sort()
                    textbook_content = []
                    
                    for pdf_name in chapter_pdfs:
                        url = f"https://archive.org/download/{item_id}/{pdf_name}"
                        pdf_path = os.path.join(grade_dir, f"{subject}_{pdf_name}")
                        txt_path = os.path.join(grade_dir, f"{subject}_{pdf_name.replace('.pdf', '.txt')}")
                        
                        if download_file(url, pdf_path):
                            if extract_pdf_text(pdf_path, txt_path):
                                with open(txt_path, 'r', encoding='utf-8') as f:
                                    txt_data = f.read()
                                
                                chapter_num = re.search(r'\d+', pdf_name)
                                chapter_str = f"Chapter {chapter_num.group()}" if chapter_num else pdf_name
                                textbook_content.append(f"## {chapter_str}\n\n{txt_data}\n\n" + "="*50 + "\n")
                                
                                try:
                                    os.remove(pdf_path)
                                    os.remove(txt_path)
                                except Exception as cleanup_err:
                                    print(f"Error cleaning up temp file {pdf_path}: {cleanup_err}")
                    
                    if textbook_content:
                        consolidated_path = os.path.join(grade_dir, f"{subject}_textbook.txt")
                        with open(consolidated_path, 'w', encoding='utf-8') as f:
                            f.write("\n\n".join(textbook_content))
                        print(f"Consolidated Class {grade} {subject} textbook to {consolidated_path}")
                        
                except Exception as e:
                    print(f"Error downloading Class {grade} {subject}: {e}")

if __name__ == '__main__':
    # 4. Download Class 1 to 5 textbooks from Internet Archive
    download_class_1_to_5()
    print("Class 1 to 5 downloads and extractions completed successfully!")
