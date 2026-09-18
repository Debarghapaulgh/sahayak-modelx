"""
wbbse_final_4.py
Direct extraction of the 4 remaining WBBSE textbooks using gdown.
"""

import io
import json
import os
import re
import sys
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from PIL import Image
import pymupdf
import pytesseract
import gdown
from stm_fast_extract import extract_pdf_stm

TESS_EXE = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESS_DATA = r"e:\Downloads\SyntheticTutor\tessdata"
pytesseract.pytesseract.tesseract_cmd = TESS_EXE
os.environ["TESSDATA_PREFIX"] = TESS_DATA

WBBSE_DIR = Path(__file__).parent / "northbengal-dataset-forge-2026-08-19" / \
            "northbengal-dataset-forge" / "raw-textbooks" / "wbbse"

REMAINING = [
    ("1ED5GxVNq_l1mZYumSS329r8dWwt3800i", "Otit O Oitijhyo Class VII.pdf", "class_7", "otit_o_oitijhyo", "otit_o_oitijhyo_7"),
    ("1Z3a3L1LoGwTUSUgTEY5koTXvf7FsGbnq", "Poribesh O Bigyan Class VIII.pdf", "class_8", "paribesh_o_bigyan", "poribesh_o_bigyan_8"),
    ("1QdXHU_AuPs3SKBOUZZy0PwGT7BFH02Bu", "Otit O Oitijhyo Class VIII.pdf", "class_8", "otit_o_oitijhyo", "otit_o_oitijhyo_8"),
    ("1i9WUTZ9daxyTBfHNh8MkcwgPnOLu-X77", "Ganit Prokash Class X.pdf", "class_10", "ganit_prakash", "ganit_prakash_10"),
]

def download_pdf_gdown(file_id: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 5000:
        return True
    try:
        url = f"https://drive.google.com/uc?id={file_id}"
        res = gdown.download(url=url, output=str(dest), quiet=False)
        if dest.exists() and dest.stat().st_size > 5000:
            return True
    except Exception as e:
        print(f"    gdown error: {e}")
    return False

def _tess_page_worker(args):
    pdf_path_str, page_num, dpi = args
    pytesseract.pytesseract.tesseract_cmd = TESS_EXE
    os.environ["TESSDATA_PREFIX"] = TESS_DATA
    doc = pymupdf.open(pdf_path_str)
    page = doc[page_num]
    pix = page.get_pixmap(dpi=dpi)
    doc.close()
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    text = pytesseract.image_to_string(img, lang="ben")
    return page_num, text.strip()

def run_parallel_tesseract(pdf_path: Path, max_workers: int = 4, dpi: int = 150) -> str:
    doc = pymupdf.open(pdf_path)
    num_pages = len(doc)
    doc.close()
    
    print(f"  Running 4x Parallel Tesseract 5.4 on {num_pages} pages...")
    tasks = [(str(pdf_path), i, dpi) for i in range(num_pages)]
    results = {}
    t0 = time.time()
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_tess_page_worker, task): task[1] for task in tasks}
        completed = 0
        for future in as_completed(futures):
            page_num, page_str = future.result()
            results[page_num] = page_str
            completed += 1
            if completed % 25 == 0 or completed == num_pages:
                dt = time.time() - t0
                rate = completed / max(1e-5, dt)
                print(f"    Completed {completed}/{num_pages} pages ({rate:.1f} pages/sec)...")
    
    pages_text = []
    for i in range(num_pages):
        page_str = results.get(i, "").strip()
        if page_str:
            pages_text.append(f"## পৃষ্ঠা {i+1}\n\n{page_str}")
    return "\n\n".join(pages_text)

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    tmp_dir = Path("C:/Temp/wbbse_pdfs")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    
    for file_id, filename, class_dir, subject_dir, slug in REMAINING:
        out_dir = WBBSE_DIR / class_dir / subject_dir
        out_txt = out_dir / f"{slug}.txt"
        
        print(f"\nProcessing final book: {filename}...")
        pdf_path = tmp_dir / f"{file_id}.pdf"
        
        if not download_pdf_gdown(file_id, pdf_path):
            print(f"  FAILED download: {filename}")
            continue
        
        t0 = time.time()
        text = extract_pdf_stm(pdf_path)
        dt = time.time() - t0
        bn_count = len(re.findall(r"[\u0980-\u09FF]", text))
        
        if bn_count > 1000:
            out_dir.mkdir(parents=True, exist_ok=True)
            out_txt.write_text(text, encoding="utf-8")
            print(f"  OK (STM decoded): {len(text):,} chars -> {out_txt.name}")
            continue
        
        t0 = time.time()
        text = run_parallel_tesseract(pdf_path, max_workers=4, dpi=150)
        dt = time.time() - t0
        bn_count = len(re.findall(r"[\u0980-\u09FF]", text))
        
        if bn_count > 100:
            out_dir.mkdir(parents=True, exist_ok=True)
            out_txt.write_text(text, encoding="utf-8")
            print(f"  OK (Tesseract 5.4 in {dt:.1f}s): {len(text):,} chars, {bn_count:,} Bengali Unicode codepoints -> {out_txt.name}")

if __name__ == "__main__":
    main()