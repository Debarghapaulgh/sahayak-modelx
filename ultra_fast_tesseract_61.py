"""
ultra_fast_tesseract_61.py
Ultra-fast (10x accelerated) Tesseract 5.4 OCR pipeline for all 61 WBBSE books.
- 8 Process Workers
- DPI = 100
- Tesseract Config: --oem 1 --psm 6 (Uniform Block Fast Mode)
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

TESS_EXE = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESS_DATA = r"e:\Downloads\SyntheticTutor\tessdata"
pytesseract.pytesseract.tesseract_cmd = TESS_EXE
os.environ["TESSDATA_PREFIX"] = TESS_DATA

WBBSE_DIR = Path(__file__).parent / "northbengal-dataset-forge-2026-08-19" / \
            "northbengal-dataset-forge" / "raw-textbooks" / "wbbse"

TESS_CONFIG = r'--oem 1 --psm 6'


def slugify(name: str) -> str:
    s = name.replace(".pdf", "").strip()
    s = re.sub(r'[\xa0\s]+', '_', s)
    s = re.sub(r'[^a-zA-Z0-9_]', '', s)
    return s.lower()


def get_target_path(filename: str) -> Path:
    slug = slugify(filename)
    
    if "class_iii" in slug or "class_3" in slug:
        c_dir = "class_3"
    elif "class_iv" in slug or "class_4" in slug:
        c_dir = "class_4"
    elif "class_v" in slug or "class_5" in slug:
        c_dir = "class_5"
    elif "class_vi" in slug or "class_6" in slug:
        c_dir = "class_6"
    elif "class_vii" in slug or "class_7" in slug:
        c_dir = "class_7"
    elif "class_viii" in slug or "class_8" in slug:
        c_dir = "class_8"
    elif "class_ix" in slug or "class_9" in slug:
        c_dir = "class_9"
    elif "class_x" in slug or "class_10" in slug:
        c_dir = "class_10"
    elif "class_xi" in slug or "class_11" in slug:
        c_dir = "class_11"
    elif "class_xii" in slug or "class_12" in slug:
        c_dir = "class_12"
    else:
        c_dir = "general"
        
    if "poribesh" in slug or "bigyan" in slug or "science" in slug:
        s_dir = "paribesh_o_bigyan"
    elif "gonit" in slug or "ganit" in slug or "math" in slug:
        s_dir = "ganit_probha" if c_dir in ["class_6", "class_7", "class_8"] else "ganit_prakash"
    elif "prithibi" in slug or "geography" in slug:
        s_dir = "amader_prithibi"
    elif "otit" in slug or "history" in slug:
        s_dir = "otit_o_oitijhyo"
    elif "bhasa" in slug or "bhasha" in slug:
        s_dir = "bhasa_chorcha"
    elif "blossoms" in slug or "bliss" in slug or "english" in slug or "butterfly" in slug or "rhapsody" in slug:
        s_dir = "english"
    else:
        s_dir = "sahitya_mela"
        
    target_folder = WBBSE_DIR / c_dir / s_dir
    target_folder.mkdir(parents=True, exist_ok=True)
    return target_folder / f"{slug}.txt"


def _tess_page_worker(args):
    pdf_path_str, page_num, dpi = args
    pytesseract.pytesseract.tesseract_cmd = TESS_EXE
    os.environ["TESSDATA_PREFIX"] = TESS_DATA
    
    try:
        doc = pymupdf.open(pdf_path_str)
        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        doc.close()
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img, lang="ben+eng", config=TESS_CONFIG)
        return page_num, text.strip()
    except Exception as e:
        return page_num, ""


def run_parallel_tesseract(pdf_path: Path, max_workers: int = 8, dpi: int = 100) -> str:
    doc = pymupdf.open(pdf_path)
    num_pages = len(doc)
    doc.close()
    
    print(f"  Accelerated Tesseract 5.4 ({max_workers} workers, {dpi} DPI, PSM 6) on {num_pages} pages...")
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
            if completed % 50 == 0 or completed == num_pages:
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
    drive_json = Path("e:/Downloads/SyntheticTutor/wbbse_drive_files.json")
    files = json.loads(drive_json.read_text(encoding="utf-8-sig"))
    
    tmp_dir = Path("C:/Temp/wbbse_pdfs")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    
    total = len(files)
    print(f"=== ULTRA-FAST TESSERACT 5.4 OCR (8 Workers, 100 DPI) FOR ALL {total} BOOKS ===")
    
    ok = 0
    start_t = time.time()
    
    for idx, f in enumerate(files, 1):
        file_id = f["id"]
        filename = f["name"]
        target_txt = get_target_path(filename)
        
        # Check if clean text file already exists
        if target_txt.exists() and target_txt.stat().st_size > 5000:
            content = target_txt.read_text(encoding="utf-8", errors="ignore")
            garbled_count = len(re.findall(r'[þßñiú]', content))
            bn_count = len(re.findall(r"[\u0980-\u09FF]", content))
            if garbled_count == 0 and (bn_count > 500 or "english" in str(target_txt).lower()):
                print(f"[{idx}/{total}] SKIP CLEAN: {target_txt.name} ({bn_count:,} Bengali codepoints)")
                ok += 1
                continue
        
        print(f"\n[{idx}/{total}] Processing: {filename} -> {target_txt.name}...")
        
        pdf_path = tmp_dir / f"{file_id}.pdf"
        if not pdf_path.exists() or pdf_path.stat().st_size < 5000:
            print(f"  Downloading from Drive ({file_id})...")
            try:
                url = f"https://drive.google.com/uc?id={file_id}"
                gdown.download(url=url, output=str(pdf_path), quiet=False)
            except Exception as e:
                print(f"  Download failed: {e}")
                continue
                
        if not pdf_path.exists() or pdf_path.stat().st_size < 5000:
            print(f"  Invalid PDF file for {filename}")
            continue
            
        t0 = time.time()
        text = run_parallel_tesseract(pdf_path, max_workers=8, dpi=100)
        dt = time.time() - t0
        
        bn_count = len(re.findall(r"[\u0980-\u09FF]", text))
        target_txt.write_text(text, encoding="utf-8")
        print(f"  OK (Tesseract in {dt:.1f}s): {len(text):,} chars, {bn_count:,} Bengali Unicode codepoints -> {target_txt.name}")
        ok += 1
        
    elapsed = time.time() - start_t
    print(f"\n=== FINISHED ALL {ok}/{total} BOOKS IN {elapsed:.1f}s ===")


if __name__ == "__main__":
    main()