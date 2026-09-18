#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
download_textbooks.py
Reads textbook_links.json and downloads all 55 textbook PDFs locally
to synthetic-corpus/raw-textbooks/ using Google Drive's direct download URL.
"""

import os
import json
import urllib.request
import sys

# Define directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINKS_JSON_PATH = os.path.join(BASE_DIR, "textbook_links.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "raw-textbooks")

def download_file(drive_id, dest_path, title):
    # Google Drive direct download URL
    url = f"https://docs.google.com/uc?export=download&id={drive_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"Downloading: {title} ...", end="", flush=True)
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response, open(dest_path, 'wb') as out_file:
            # Check if we got redirected to a confirmation page
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                html = response.read().decode('utf-8', errors='ignore')
                # Try to extract the confirmation token for large files
                confirm_token = None
                match = re.search(r'confirm=([a-zA-Z0-9-_]+)', html)
                if match:
                    confirm_token = match.group(1)
                    confirm_url = f"https://docs.google.com/uc?export=download&id={drive_id}&confirm={confirm_token}"
                    req_confirm = urllib.request.Request(confirm_url, headers=headers)
                    with urllib.request.urlopen(req_confirm) as res_confirm:
                        out_file.write(res_confirm.read())
                else:
                    # Google Drive might have rate-limited or blocked direct download
                    print(" [Requires manual confirmation or browser download]")
                    return False
            else:
                out_file.write(response.read())
        print(" [Success]")
        return True
    except Exception as e:
        print(f" [Failed: {e}]")
        return False

def main():
    if not os.path.exists(LINKS_JSON_PATH):
        print(f"Error: {LINKS_JSON_PATH} not found. Please run scrape_textbook_links.py first.")
        sys.exit(1)
        
    with open(LINKS_JSON_PATH, "r", encoding="utf-8") as f:
        database = json.load(f)
        
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    total_books = sum(len(books) for books in database.values())
    print(f"Found {total_books} books to download. Target folder: {OUTPUT_DIR}\n")
    
    downloaded = 0
    failed = 0
    
    for class_name, books in database.items():
        class_dir = os.path.join(OUTPUT_DIR, class_name)
        os.makedirs(class_dir, exist_ok=True)
        
        print(f"--- Downloading books for {class_name.replace('_', ' ').title()} ---")
        for book in books:
            drive_id = book["drive_id"]
            # Clean filename
            safe_title = "".join(c for c in book["title"] if c.isalnum() or c in (' ', '_', '-')).strip()
            dest_filename = f"{safe_title}.pdf".replace(" ", "_")
            dest_path = os.path.join(class_dir, dest_filename)
            
            if os.path.exists(dest_path):
                print(f"File already exists: {book['title']} (Skipping)")
                downloaded += 1
                continue
                
            success = download_file(drive_id, dest_path, book["title"])
            if success:
                downloaded += 1
            else:
                failed += 1
                
    print(f"\nDownload summary: {downloaded} downloaded, {failed} failed.")

if __name__ == "__main__":
    import re # import inside main scope to ensure regex works
    main()
