#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
transfer_textbooks.py
Programmatic Google Drive API copy script.
Copies the 55 textbook PDFs directly from the source IDs to the target folder
(1GPhEf3VDWJvNpX6jeGXDn_Rd3IXWaLOY) on your Google Drive using your own credentials.
"""

import os
import json
import sys

# Define directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINKS_JSON_PATH = os.path.join(BASE_DIR, "textbook_links.json")
TARGET_FOLDER_ID = "1GPhEf3VDWJvNpX6jeGXDn_Rd3IXWaLOY"

def check_dependencies():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        return True
    except ImportError:
        print("Required libraries missing. Please run:")
        print("  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return False

def main():
    if not check_dependencies():
        sys.exit(1)
        
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    
    if not os.path.exists(LINKS_JSON_PATH):
        print(f"Error: {LINKS_JSON_PATH} not found. Run scrape_textbook_links.py first.")
        sys.exit(1)
        
    with open(LINKS_JSON_PATH, "r", encoding="utf-8") as f:
        database = json.load(f)
        
    print("--- Google Drive Bulk Textbook Copier ---")
    print(f"Destination Folder ID: {TARGET_FOLDER_ID}")
    print("This script requires a 'credentials.json' file downloaded from your Google Cloud Console.")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a project, enable the Google Drive API.")
    print("3. Configure OAuth Consent Screen (External) and add yourself as a test user.")
    print("4. Create OAuth Client ID credentials (Desktop app) and download credentials.json.")
    print("5. Put credentials.json in this directory and run the script.")
    
    # Check for credentials.json in root workspace directory first, fallback to BASE_DIR
    root_dir = os.path.dirname(BASE_DIR)
    cred_file = os.path.join(root_dir, "credentials.json")
    if not os.path.exists(cred_file):
        cred_file = os.path.join(BASE_DIR, "credentials.json")
        
    if not os.path.exists(cred_file):
        print(f"\nError: credentials.json not found in the project root directory ({root_dir}) or {BASE_DIR}. Copying cannot proceed.")
        sys.exit(1)
        
    # Standard desktop OAuth2 flow
    scopes = ['https://www.googleapis.com/auth/drive']
    flow = InstalledAppFlow.from_client_secrets_file(cred_file, scopes)
    creds = flow.run_local_server(port=0)
    service = build('drive', 'v3', credentials=creds)
    
    total_books = sum(len(books) for books in database.values())
    print(f"\nAuthenticated successfully. Copying {total_books} books...\n")
    
    # Retrieve names of files already in target folder to prevent duplicates
    existing_files = set()
    try:
        query = f"'{TARGET_FOLDER_ID}' in parents and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(name)"
        ).execute()
        for f in results.get('files', []):
            existing_files.add(f.get('name'))
        print(f"Found {len(existing_files)} existing files in the destination folder.")
    except Exception as e:
        print(f"Warning: could not query existing folder files ({e}). Duplicates might occur.")
        
    copied = 0
    skipped = 0
    failed = 0
    
    for class_name, books in database.items():
        print(f"\nProcessing {class_name.replace('_', ' ').title()}...")
        for book in books:
            drive_id = book["drive_id"]
            title = book["title"]
            dest_name = f"{title}.pdf"
            
            if dest_name in existing_files:
                print(f"  Already exists: {title} (Skipping)")
                skipped += 1
                continue
                
            try:
                # Copy file directly inside Google Drive to the target folder
                copied_file_metadata = {
                    'name': dest_name,
                    'parents': [TARGET_FOLDER_ID]
                }
                service.files().copy(
                    fileId=drive_id,
                    body=copied_file_metadata
                ).execute()
                print(f"  Successfully copied: {title}")
                copied += 1
            except Exception as e:
                print(f"  Failed to copy: {title} ({e})")
                failed += 1
                
    print(f"\nTransfer complete! {copied} successfully copied, {skipped} skipped, {failed} failed.")

if __name__ == "__main__":
    main()
