"""
wbbse_extract.py
Downloads each PDF from the public Google Drive folder, sends it to Gemini
for Bengali OCR extraction, and saves .txt files to raw-textbooks/wbbse/.

Usage:
    python wbbse_extract.py              # extract all books
    python wbbse_extract.py --dry-run    # print plan only
    python wbbse_extract.py --id <id>    # single file test
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from google import genai
from google.genai import types

# ── config ────────────────────────────────────────────────────────────────── #
API_KEY = "AQ.Ab8RN6LLOx5asLGNsgnFjUI-xDsuC5wK-i43y7WT_442CRlTVQ"
WBBSE_DIR = Path(__file__).parent / "northbengal-dataset-forge-2026-08-19" / \
            "northbengal-dataset-forge" / "raw-textbooks" / "wbbse"

BOOK_MAP = {
    # Class 6
    "Poribesh O Bigyan Class VI.pdf":     ("class_6", "paribesh_o_bigyan", "poribesh_o_bigyan_6"),
    "Ganit Probha Class VI.pdf":          ("class_6", "ganit_probha",      "ganit_probha_6"),
    "Otit O Oitijhyo Class VI.pdf":       ("class_6", "otit_o_oitijhyo",   "otit_o_oitijhyo_6"),
    "Amader Prithibi Class VI.pdf":       ("class_6", "amader_prithibi",   "amader_prithibi_6"),
    "Sahitya Mela Class VI.pdf":          ("class_6", "sahitya_mela",      "sahitya_mela_6"),
    "Bhasa Charcha Class VI.pdf":         ("class_6", "bhasa_chorcha",     "bhasa_chorcha_6"),
    # Class 7
    "Poribesh O Bigyan Class VII.pdf":    ("class_7", "paribesh_o_bigyan", "poribesh_o_bigyan_7"),
    "Ganit Probha Class VII.pdf":         ("class_7", "ganit_probha",      "ganit_probha_7"),
    "Otit O Oitijhyo Class VII.pdf":      ("class_7", "otit_o_oitijhyo",   "otit_o_oitijhyo_7"),
    "Amader Prithibi Class VII.pdf":      ("class_7", "amader_prithibi",   "amader_prithibi_7"),
    "Sahitya Mela Class VII.pdf":         ("class_7", "sahitya_mela",      "sahitya_mela_7"),
    # Class 8
    "Poribesh O Bigyan Class VIII.pdf":   ("class_8", "paribesh_o_bigyan", "poribesh_o_bigyan_8"),
    "Ganit Probha Class VIII.pdf":        ("class_8", "ganit_probha",      "ganit_probha_8"),
    "Otit O Oitijhyo Class VIII.pdf":     ("class_8", "otit_o_oitijhyo",   "otit_o_oitijhyo_8"),
    "Amader Prithibi Class VIII.pdf":     ("class_8", "amader_prithibi",   "amader_prithibi_8"),
    "Sahitya Mela Class VIII.pdf":        ("class_8", "sahitya_mela",      "sahitya_mela_8"),
    "Bhasa Charcha Class VIII.pdf":       ("class_8", "bhasa_chorcha",     "bhasa_chorcha_8"),
    # Class 9
    "Ganit Prokash Class IX.pdf":         ("class_9", "ganit_prakash",     "ganit_prakash_9"),
    "Sahity Sanchayan Class IX.pdf":      ("class_9", "sahitya_sanchayan", "sahitya_sanchayan_9"),
    "Bliss Class IX.pdf":                 ("class_9", "bliss",             "bliss_9"),
    # Class 10
    "Ganit Prokash Class X.pdf":          ("class_10", "ganit_prakash",    "ganit_prakash_10"),
    "Bliss Class X.pdf":                  ("class_10", "bliss",            "bliss_10"),
}

EXTRACT_PROMPT = """You are extracting text from a WBBSE Bengali-medium textbook PDF.

Rules:
1. Extract ALL text preserving Bengali script (বাংলা) exactly.
2. Chapter titles → # অধ্যায় N: <title>
3. Section headings → ## <heading>
4. Sub-sections → ### <sub-heading>
5. Tables → pipe-separated rows.
6. Math formulae → write as printed (e.g. a² + b² = c²).
7. Figures/diagrams → [চিত্র N.M] placeholder only, skip image.
8. Page headers / footers / page numbers → SKIP.
9. Publisher notice, copyright, ISBN pages → SKIP.
10. Write ONLY Bengali script + numbers/symbols. Do NOT translate. Do NOT add English.

Output the full extracted text:"""


def download_pdf(file_id: str, dest: Path) -> bool:
    url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm=1"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, stream=True, timeout=120, headers=headers)
        content = b"".join(r.iter_content(chunk_size=8192))
        if r.status_code == 200 and len(content) > 5000:
            # Check if we got a confirm page instead of the PDF
            if b"%PDF" not in content[:10]:
                confirm = re.search(rb'confirm=([0-9A-Za-z_-]+)', content)
                if confirm:
                    url2 = f"https://drive.google.com/uc?export=download&id={file_id}&confirm={confirm.group(1).decode()}"
                    r2 = requests.get(url2, stream=True, timeout=120, headers=headers)
                    content = b"".join(r2.iter_content(chunk_size=8192))
            if b"%PDF" in content[:10]:
                dest.write_bytes(content)
                return True
    except Exception as e:
        print(f"    Download error: {e}")
    return False


def extract_text(pdf_path: Path) -> str:
    client = genai.Client(api_key=API_KEY)
    
    print(f"    Uploading {pdf_path.name} ({pdf_path.stat().st_size // 1024} KB)...")
    with open(pdf_path, "rb") as f:
        uploaded = client.files.upload(
            file=f,
            config={"mime_type": "application/pdf", "display_name": pdf_path.name}
        )
    
    # Wait for ACTIVE state
    for _ in range(30):
        status = client.files.get(name=uploaded.name)
        if status.state.name == "ACTIVE":
            break
        time.sleep(2)
    
    print(f"    Extracting text via Gemini 2.0 Flash...")
    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Part.from_uri(file_uri=uploaded.uri, mime_type="application/pdf"),
            EXTRACT_PROMPT,
        ],
        config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=8192),
    )
    
    try:
        client.files.delete(name=uploaded.name)
    except Exception:
        pass
    
    return resp.text


def process_book(file_id: str, filename: str, class_dir: str, subject_dir: str,
                 slug: str, dry_run: bool = False) -> bool:
    out_dir = WBBSE_DIR / class_dir / subject_dir
    out_txt = out_dir / f"{slug}.txt"
    
    if out_txt.exists() and out_txt.stat().st_size > 500:
        print(f"  SKIP (exists): {out_txt.relative_to(WBBSE_DIR)}")
        return True
    
    print(f"\n{'[DRY] ' if dry_run else ''}Book: {filename}")
    print(f"  -> {class_dir}/{subject_dir}/{slug}.txt")
    
    if dry_run:
        return True
    
    tmp = Path("C:/Temp") / f"{file_id}.pdf"
    tmp.parent.mkdir(exist_ok=True)
    
    print(f"  Downloading...")
    if not download_pdf(file_id, tmp):
        print(f"  FAILED download")
        return False
    print(f"  Downloaded: {tmp.stat().st_size // 1024} KB")
    
    try:
        text = extract_text(tmp)
    except Exception as e:
        print(f"  FAILED extraction: {e}")
        return False
    finally:
        tmp.unlink(missing_ok=True)
    
    if len(text.strip()) < 200:
        print(f"  WARNING: short output ({len(text)} chars)")
        return False
    
    out_dir.mkdir(parents=True, exist_ok=True)
    out_txt.write_text(text, encoding="utf-8")
    bn = len(re.findall(r"[\u0980-\u09FF]", text))
    print(f"  OK: {len(text):,} chars, {bn:,} Bengali codepoints -> {out_txt.name}")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--id", help="Single file ID to process")
    args = ap.parse_args()
    
    drive_json = Path("e:/Downloads/SyntheticTutor/wbbse_drive_files.json")
    files = json.loads(drive_json.read_text(encoding="utf-8-sig"))  # handle BOM
    name_to_id = {f["name"]: f["id"] for f in files}
    
    ok = fail = 0
    for filename, (class_dir, subject_dir, slug) in BOOK_MAP.items():
        file_id = name_to_id.get(filename)
        if not file_id:
            print(f"  NOT IN DRIVE: {filename}")
            fail += 1
            continue
        if args.id and file_id != args.id:
            continue
        result = process_book(file_id, filename, class_dir, subject_dir, slug, args.dry_run)
        if result:
            ok += 1
        else:
            fail += 1
        if not args.dry_run:
            time.sleep(4)
    
    print(f"\n=== {ok} ok  {fail} failed ===")


if __name__ == "__main__":
    main()