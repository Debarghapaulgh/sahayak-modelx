#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_textbook_text.py
Extracts and structures page-by-page text from WBBSE PDFs.
Aligns pages to chapter lists from north-bengal.json.
Saves output to synthetic-corpus/textbook_chapters_text.json.
"""

import os
import sys
import json
import pdfplumber
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALE_PACK_PATH = os.path.join(BASE_DIR, "locale-packs", "north-bengal.json")
RAW_TEXTBOOKS_DIR = os.path.join(BASE_DIR, "raw-textbooks")
OUTPUT_JSON_PATH = os.path.join(BASE_DIR, "textbook_chapters_text.json")

def load_locale_pack():
    with open(LOCALE_PACK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# Subject matching keywords in filenames
SUBJECT_KEYWORDS = {
    "math": ["ganit", "mathematics", "prokash", "probha"],
    "science": ["poribesh", "bigyan", "science"],
    "physical_science": ["poribesh", "bigyan", "physical", "science"],
    "life_science": ["poribesh", "bigyan", "life", "science"],
    "bengali": ["sahitya", "patabahar", "sahoj", "bengali", "sanchayan", "mela", "charcha"],
    "english": ["blossoms", "bliss", "butterfly", "english"],
    "history": ["otit", "oitijhyo", "history", "ateet", "aitihya"],
    "geography": ["prithibi", "geography"]
}

def find_pdf_for_subject(class_name, subject):
    class_dir = os.path.join(RAW_TEXTBOOKS_DIR, class_name)
    if not os.path.exists(class_dir):
        return None
        
    keywords = SUBJECT_KEYWORDS.get(subject, [subject])
    
    for filename in os.listdir(class_dir):
        if filename.endswith(".pdf"):
            lower_name = filename.lower()
            if any(kw in lower_name for kw in keywords):
                return os.path.join(class_dir, filename)
    return None

def clean_text(text):
    if not text:
        return ""
    # Clean excessive spaces and correct newline boundaries
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()

def extract_pdf_pages(pdf_path):
    print(f"Extracting text from: {os.path.basename(pdf_path)}...")
    pages_text = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for idx, page in enumerate(pdf.pages):
                text = page.extract_text()
                pages_text.append({
                    "page_number": idx + 1,
                    "text": clean_text(text)
                })
    except Exception as e:
        print(f"  Error reading PDF {pdf_path}: {e}")
    return pages_text

def segment_chapters(pages_text, chapters):
    if not pages_text or not chapters:
        return {}
        
    chapter_segments = {}
    chapter_start_pages = []
    
    # 1. Identify starting page for each chapter using keyword match
    for ch in chapters:
        # Search for exact or close chapter name in pages
        clean_ch = ch.strip()
        found_page = None
        for p in pages_text:
            if p["text"] and clean_ch in p["text"]:
                found_page = p["page_number"]
                break
        
        # Fallback: Search for individual terms if not found directly
        if not found_page:
            ch_words = [w for w in re.split(r'\W+', clean_ch) if len(w) > 2]
            if ch_words:
                for p in pages_text:
                    if p["text"] and all(w in p["text"] for w in ch_words):
                        found_page = p["page_number"]
                        break
                        
        if found_page:
            chapter_start_pages.append((ch, found_page))
            
    # Sort detected chapters by page order
    chapter_start_pages.sort(key=lambda x: x[1])
    
    # 2. Extract page ranges for each chapter
    for idx, (ch, start_page) in enumerate(chapter_start_pages):
        end_page = pages_text[-1]["page_number"]
        if idx + 1 < len(chapter_start_pages):
            end_page = chapter_start_pages[idx + 1][1] - 1
            
        # Collect text in range
        ch_text_blocks = []
        for p in pages_text:
            if start_page <= p["page_number"] <= end_page:
                if p["text"]:
                    ch_text_blocks.append(p["text"])
                    
        chapter_segments[ch] = {
            "start_page": start_page,
            "end_page": end_page,
            "text": "\n".join(ch_text_blocks)
        }
        
    # 3. For any chapters that weren't located, assign a fallback semantic block
    # using simple term frequency matching across all pages
    for ch in chapters:
        if ch not in chapter_segments:
            # Score pages based on term occurrence
            ch_words = [w for w in re.split(r'\W+', ch) if len(w) > 2]
            best_pages = []
            if ch_words:
                scored_pages = []
                for p in pages_text:
                    if not p["text"]:
                        continue
                    score = sum(1 for w in ch_words if w in p["text"])
                    if score > 0:
                        scored_pages.append((p, score))
                # Take top 3 scoring pages
                scored_pages.sort(key=lambda x: x[1], reverse=True)
                best_pages = [x[0] for x in scored_pages[:3]]
                
            if best_pages:
                best_pages.sort(key=lambda x: x["page_number"])
                text = "\n".join(p["text"] for p in best_pages)
                chapter_segments[ch] = {
                    "start_page": best_pages[0]["page_number"],
                    "end_page": best_pages[-1]["page_number"],
                    "text": text,
                    "is_fallback": True
                }
            else:
                chapter_segments[ch] = {
                    "start_page": None,
                    "end_page": None,
                    "text": "",
                    "is_fallback": False
                }
                
    return chapter_segments

def main():
    pack = load_locale_pack()
    
    extracted_database = {}
    
    # We will loop over the syllabus configuration
    # The syllabus keys are like "math_grade5", "science_grade6", etc.
    syllabus = pack.get("syllabus", {})
    
    total_chapters_processed = 0
    total_chapters_matched = 0
    
    for syllabus_key, chapters in syllabus.items():
        if syllabus_key == "note":
            continue
            
        # Parse grade and subject from syllabus key (e.g. math_grade5)
        match = re.match(r'([a-z_]+)_grade(\d+)', syllabus_key)
        if not match:
            continue
            
        subject = match.group(1)
        grade = int(match.group(2))
        class_name = f"class_{grade}"
        
        pdf_path = find_pdf_for_subject(class_name, subject)
        if not pdf_path or not os.path.exists(pdf_path):
            print(f"Skipping {syllabus_key}: Local PDF not found.")
            continue
            
        # Parse PDF
        pages_text = extract_pdf_pages(pdf_path)
        if not pages_text:
            continue
            
        # Aligns pages to chapter lists
        chapter_segments = segment_chapters(pages_text, chapters)
        
        # Save to database
        if class_name not in extracted_database:
            extracted_database[class_name] = {}
        extracted_database[class_name][subject] = chapter_segments
        
        # Print progress
        matched = sum(1 for ch in chapters if ch in chapter_segments and chapter_segments[ch]["text"])
        total_chapters_processed += len(chapters)
        total_chapters_matched += matched
        print(f"  Processed {len(chapters)} chapters. Matched {matched} to PDF text content.\n")
        
    # Write to final JSON file
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(extracted_database, f, ensure_ascii=False, indent=2)
        
    print(f"Extraction complete! Aligned {total_chapters_matched}/{total_chapters_processed} chapters.")
    print(f"Chapter text database saved to {OUTPUT_JSON_PATH}")

if __name__ == "__main__":
    main()
