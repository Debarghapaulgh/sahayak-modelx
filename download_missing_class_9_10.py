"""
download_missing_class_9_10.py
Attempts to download missing WBBSE Class 9 & 10 textbooks from Banglar Shiksha / WBBSE mirrors.
"""

import re
import sys
import requests
from pathlib import Path

MISSING_BOOKS = [
    ("Class 9 History", "https://banglarshiksha.gov.in/frontend/e_textbook_class9_history.pdf", "class_9", "otit_o_oitijhyo", "otit_o_oitijhyo_9.pdf"),
    ("Class 9 Geography", "https://banglarshiksha.gov.in/frontend/e_textbook_class9_geography.pdf", "class_9", "amader_prithibi", "amader_prithibi_9.pdf"),
    ("Class 9 Physical Science", "https://banglarshiksha.gov.in/frontend/e_textbook_class9_physical_science.pdf", "class_9", "paribesh_o_bigyan", "poribesh_o_bigyan_9.pdf"),
    ("Class 9 Life Science", "https://banglarshiksha.gov.in/frontend/e_textbook_class9_life_science.pdf", "class_9", "paribesh_o_bigyan", "jibon_bigyan_9.pdf"),
    ("Class 10 History", "https://banglarshiksha.gov.in/frontend/e_textbook_class10_history.pdf", "class_10", "otit_o_oitijhyo", "otit_o_oitijhyo_10.pdf"),
    ("Class 10 Geography", "https://banglarshiksha.gov.in/frontend/e_textbook_class10_geography.pdf", "class_10", "amader_prithibi", "amader_prithibi_10.pdf"),
    ("Class 10 Physical Science", "https://banglarshiksha.gov.in/frontend/e_textbook_class10_physical_science.pdf", "class_10", "paribesh_o_bigyan", "poribesh_o_bigyan_10.pdf"),
    ("Class 10 Life Science", "https://banglarshiksha.gov.in/frontend/e_textbook_class10_life_science.pdf", "class_10", "paribesh_o_bigyan", "jibon_bigyan_10.pdf"),
]

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    tmp_dir = Path("C:/Temp/wbbse_pdfs")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for title, url, c_dir, s_dir, filename in MISSING_BOOKS:
        dest = tmp_dir / filename
        print(f"Checking {title} -> {url}...")
        try:
            r = requests.get(url, stream=True, timeout=15, headers=headers)
            if r.status_code == 200 and len(r.content) > 5000:
                dest.write_bytes(r.content)
                print(f"  SUCCESS downloaded {title} ({len(r.content):,} bytes)!")
            else:
                print(f"  Status {r.status_code}: Direct link unavailable on primary host.")
        except Exception as e:
            print(f"  Fetch error: {e}")

if __name__ == "__main__":
    main()