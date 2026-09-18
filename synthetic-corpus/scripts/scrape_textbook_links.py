#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scrape_textbook_links.py
Scrapes all textbook PDF download links from wbbsebooks.com for Classes 1 to 10
and saves them to a structured JSON database.
"""

import os
import re
import json
import urllib.request
from bs4 import BeautifulSoup

def get_page_html(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_drive_id(url):
    # Match drive file/open IDs
    match = re.search(r'(?:id=|\/d\/|open\?id=)([a-zA-Z0-9-_]{25,})', url)
    if match:
        return match.group(1)
    return None

def scrape_class_page(class_num):
    url = f"https://wbbsebooks.com/wbbse-books-for-class-{class_num}-pdf/"
    html = get_page_html(url)
    if not html:
        # Fallback for alternative URL schemes
        if class_num == 9:
            url = "https://wbbsebooks.com/wbbse-books-for-class-ix-pdf/" # check ix scheme
            html = get_page_html(url)
        if not html:
            return []

    soup = BeautifulSoup(html, 'html.parser')
    books = []
    
    # WBBSEBooks typically lists books in tables or standard list bullet points
    # Let's search all links pointing to Google Drive
    links = soup.find_all('a', href=True)
    for link in links:
        href = link['href']
        if 'drive.google.com' in href:
            drive_id = extract_drive_id(href)
            if drive_id:
                # Find title: try text of the link, or the parent elements
                title = link.get_text().strip()
                if not title or len(title) < 3 or 'download' in title.lower():
                    # Fallback to sibling or parent text
                    parent_text = link.parent.get_text().strip()
                    # Clean up parent text to make a title
                    title = parent_text.split('\n')[0].replace("Download", "").replace("PDF", "").strip()
                
                # Deduplicate by drive_id
                if not any(b['drive_id'] == drive_id for b in books):
                    books.append({
                        "title": title or f"Class {class_num} Book",
                        "url": href,
                        "drive_id": drive_id
                    })
                    
    print(f"Class {class_num}: Found {len(books)} books.")
    return books

def main():
    database = {}
    print("Starting WBBSE Textbook Link Scraper...")
    
    # Loop over Classes 1 to 10
    for c in range(1, 11):
        books = scrape_class_page(c)
        if books:
            database[f"class_{c}"] = books
            
    # Save database to JSON
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "textbook_links.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
        
    print(f"\nScraping complete. Saved {sum(len(b) for b in database.values())} book links to {output_path}")

if __name__ == "__main__":
    main()
