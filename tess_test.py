import io
import os
import re
import sys
import time
from pathlib import Path
from PIL import Image
import pymupdf
import pytesseract

sys.stdout.reconfigure(encoding="utf-8")
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"e:\Downloads\SyntheticTutor\tessdata"

doc = pymupdf.open("test_book.pdf")
print(f"Benchmarking Tesseract 5.4 on 10 pages of test_book.pdf...")

t0 = time.time()
pages_text = []

for i in range(min(10, len(doc))):
    page = doc[i]
    pix = page.get_pixmap(dpi=150)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    text = pytesseract.image_to_string(img, lang="ben")
    if text.strip():
        pages_text.append(text)

dt = time.time() - t0
print(f"\nDONE 10 pages in {dt:.2f} seconds ({dt/10:.2f}s/page)!")

sample = pages_text[5] if len(pages_text) > 5 else pages_text[0]
bn_count = len(re.findall(r"[\u0980-\u09FF]", sample))
print(f"\nSample Page (Bengali codepoints: {bn_count}):")
print(sample[:400])