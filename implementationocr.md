# Implementation Plan — WBBSE Textbook Extraction Pipeline Using EasyOCR

## Purpose

Rebuild the WBBSE textbook grounding dataset from the **original downloaded textbook files** rather than continuing from the previously extracted/generated dataset.

The goal of this stage is **source extraction only**.

Do NOT generate SFT questions or assistant answers yet.

The output of this pipeline must be a clean, traceable, page-aware textbook corpus that can safely feed the later source-grounded SFT regeneration pipeline.

The pipeline must be designed to prevent the previous failure mode:

> corrupted/incomplete textbook extraction → plausible-looking source chunk → LLM invents missing information.

The extraction pipeline must therefore be **conservative and rejection-oriented**.

---

# 1. Inputs

The WBBSE books have already been downloaded locally.

The pipeline must recursively discover textbook files from a configurable source directory.

Expected source formats may include:

- PDF
- scanned PDF
- image-based PDF
- JPG/JPEG/PNG page scans

The pipeline must not assume that all PDFs have usable text layers.

For each input book, preserve:

```text
source_file
source_file_hash
book_id
subject
grade
book_title
language
board
```

Do not infer subject/grade solely from filename when stronger evidence exists inside the book.

---

# 2. Output Directory Structure

Use a deterministic directory structure:

```text
datasets/
└── extraction/
    ├── raw_pages/
    │   └── <book_id>/
    │       ├── page_0001.png
    │       ├── page_0002.png
    │       └── ...
    │
    ├── ocr_raw/
    │   └── <book_id>/
    │       ├── page_0001.json
    │       ├── page_0002.json
    │       └── ...
    │
    ├── ocr_normalized/
    │   └── <book_id>/
    │       ├── page_0001.json
    │       └── ...
    │
    ├── structural_blocks/
    │   └── <book_id>.jsonl
    │
    ├── source_chunks/
    │   └── wbbse_grounding_chunks_v2.jsonl
    │
    ├── rejected/
    │   ├── rejected_pages.jsonl
    │   ├── rejected_blocks.jsonl
    │   └── rejected_chunks.jsonl
    │
    └── manifests/
        ├── books_manifest.json
        ├── extraction_manifest.json
        └── extraction_summary.json
```

Never overwrite raw OCR output.

---

# 3. Phase 0 — Book Inventory

Before OCR, scan all downloaded books and produce:

```text
books_manifest.json
```

Each book should receive:

```json
{
  "book_id": "...",
  "source_path": "...",
  "sha256": "...",
  "file_type": "pdf",
  "page_count": 250,
  "subject": "...",
  "grade": "...",
  "title": "...",
  "language": "Bengali",
  "board": "WBBSE"
}
```

If subject/grade cannot be confidently determined:

```text
metadata_status = NEEDS_REVIEW
```

Do not guess.

---

# 4. Phase 1 — PDF/Page Rendering

For scanned PDFs, render every page to a sufficiently high-resolution image before OCR.

Recommended default:

```text
DPI: 300
```

For small Bengali text or poor scans, allow:

```text
DPI: 350–400
```

Do not immediately preprocess every page aggressively.

Keep the original page image.

Create deterministic page IDs:

```text
<book_id>_page_0001
```

Preserve the original PDF page index separately from the printed page number.

These are NOT necessarily the same.

Store:

```json
{
  "book_page_index": 17,
  "printed_page_number": "15",
  "image_path": "...",
  "width": 2480,
  "height": 3508
}
```

---

# 5. Phase 2 — EasyOCR Configuration

Use EasyOCR primarily for Bengali and English mixed textbook content.

Initial reader:

```python
easyocr.Reader(
    ['bn', 'en'],
    gpu=True,
    verbose=True
)
```

If GPU is unavailable, support CPU mode.

Do not hard-code GPU availability.

The pipeline must record:

```text
ocr_engine
ocr_version
model/language configuration
device
```

for reproducibility.

---

# 6. EasyOCR Must Preserve Bounding Boxes

Do not save only plain text.

For every OCR detection preserve:

```json
{
  "bbox": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
  "text": "...",
  "confidence": 0.96
}
```

The raw OCR page record should contain:

```json
{
  "book_id": "...",
  "page_index": 17,
  "detections": [...]
}
```

Bounding boxes are required later for:

- reading order
- columns
- headings
- captions
- tables
- footnotes
- questions
- diagrams
- page-number removal

---

# 7. Do Not Treat OCR Confidence as Truth

EasyOCR confidence is useful as a signal, not as a correctness guarantee.

Do not use:

```text
confidence >= 0.8 → automatically valid
```

as the only quality criterion.

Bengali OCR can produce plausible-looking but semantically wrong text with high confidence.

Use confidence together with:

```text
Bengali character validity
language-model coherence
dictionary/term checks
structural consistency
neighboring lines
page layout
cross-page continuity
```

---

# 8. Phase 3 — Page Image Preprocessing

Use preprocessing selectively.

Possible preprocessing pipeline:

```text
original
↓
grayscale
↓
deskew
↓
contrast normalization
↓
mild denoise
↓
optional adaptive threshold
```

Do NOT use aggressive thresholding as the default.

Maintain multiple OCR attempts only for pages that fail quality checks.

For example:

```text
OCR attempt 1 = original
OCR attempt 2 = grayscale/contrast
OCR attempt 3 = deskewed/thresholded
```

If an alternate attempt is clearly better, retain it.

Do not generate multiple competing versions for every page unnecessarily.

---

# 9. Phase 4 — OCR Quality Gate

Each page receives:

```text
OCR_STATUS:
    HIGH
    ACCEPTABLE
    REVIEW
    FAIL
```

Quality signals should include:

### Text density

Pages with almost no text may be:

- covers
- diagrams
- blank pages
- image-heavy pages

Do not treat those automatically as OCR failures.

### Bengali character ratio

Estimate whether the detected text looks like Bengali where Bengali is expected.

### Garbage indicators

Detect:

- excessive Latin garbage
- long digit strings
- repeated punctuation
- malformed Unicode
- replacement characters
- random isolated symbols
- implausible consonant sequences
- broken graphemes
- impossible control characters

### OCR confidence distribution

Record:

```text
mean_confidence
median_confidence
low_confidence_ratio
```

### Structural coherence

Check whether lines form plausible prose rather than disconnected OCR fragments.

---

# 10. Phase 5 — Unicode Normalization

Normalize extracted text using safe Unicode normalization.

Recommended:

```python
unicodedata.normalize("NFC", text)
```

Do not blindly delete zero-width characters.

Some Bengali orthographic sequences may require them.

Instead classify:

```text
valid orthographic ZWJ/ZWNJ
suspicious ZWJ/ZWNJ
invalid control
```

Remove only demonstrably invalid control characters.

---

# 11. Phase 6 — Bengali OCR Error Detection

Implement a Bengali-specific error detector.

It should flag patterns such as:

```text
random Bengali consonant clusters
unexpected Latin inserted into Bengali words
Bengali + Latin collisions
isolated punctuation inside words
repeated characters
digit substitutions
visually confused Bengali glyphs
```

Examples that should trigger review:

```text
আমাদেরKulik
বেজকু
জ্াকোল
বীজগাদিডিকগরতিযা
```

Do not automatically repair these.

Mark them as:

```text
OCR_SUSPECT
```

---

# 12. Phase 7 — Layout Reconstruction

EasyOCR returns detections, not proper textbook structure.

Reconstruct reading order using bounding boxes.

Handle:

- single-column pages
- two-column pages
- multi-column textbook layouts
- headings
- subheadings
- bullet lists
- numbered exercises
- captions
- tables
- marginal notes
- footnotes

Basic reading-order heuristic:

```text
group detections into lines
→ sort by vertical position
→ detect columns
→ read top-to-bottom within each column
→ merge columns in natural reading order
```

Do not assume every page is single-column.

---

# 13. Phase 8 — Remove Page Furniture

Detect and separate:

- printed page numbers
- running headers
- running footers
- book titles repeated on every page
- chapter headers repeated on every page

Do not simply delete all short lines.

A short line may be a meaningful heading.

Store page furniture separately:

```text
page_header
page_footer
page_number
```

---

# 14. Phase 9 — Preserve Tables and Special Structures

Do not flatten everything into plain paragraphs.

Tables should retain structure where possible.

Similarly preserve:

- question numbers
- answer choices
- equations
- mathematical expressions
- diagrams/captions
- chapter titles
- examples
- exercises

For mathematics/science, OCR text must not destroy symbols.

Examples:

```text
x²
√x
a/b
∠ABC
∴
∵
H₂O
CO₂
```

must be treated as structured mathematical/scientific text.

---

# 15. Math/Science OCR Validation

Mathematical/scientific OCR requires special handling.

Detect:

```text
fractions
superscripts
subscripts
Greek letters
operators
degree signs
roots
variables
equations
chemical formulae
```

Run specialized checks.

Examples:

```text
x^2
x²
H₂O
CO₂
∠ABC
```

must not be mistaken for corrupted ASCII/Unicode.

Do not apply the Bengali-number validator to mathematical spans.

---

# 16. Phase 10 — Cross-Page Continuity

This is mandatory.

Do not treat each page as an isolated document.

Many textbook paragraphs continue:

```text
page N
→ page N+1
```

A source chunk may need content from both pages.

Detect continuation when:

- previous page ends mid-sentence
- next page begins with lowercase continuation text
- punctuation indicates continuation
- heading hierarchy continues
- paragraph boundaries do not close

Create a page-linked representation:

```text
previous_page
current_page
next_page
```

This is essential to prevent the “Arup's method” problem.

---

# 17. Phase 11 — Structural Segmentation

After OCR, segment the book into:

```text
Book
  → Chapter
      → Section
          → Subsection
              → Explanation
              → Example
              → Exercise
              → Activity
```

Use:

1. explicit headings where detected,
2. typography/layout signals,
3. numbering patterns,
4. cross-page continuity.

Do not ask an LLM to invent chapters when the source does not establish them.

---

# 18. Canonical Metadata

Each structural block should contain:

```json
{
  "book_id": "...",
  "subject": "...",
  "grade": 8,
  "chapter": "...",
  "section": "...",
  "topic": "...",
  "page_start": 72,
  "page_end": 73,
  "source_text": "...",
  "source_quality": "HIGH"
}
```

Important:

`topic` must be derived from the actual textbook structure.

Do not use arbitrary OCR fragments as topic names.

---

# 19. Source Sufficiency Check

Before a block becomes a grounding chunk, ask:

> Can an independent reader understand the content without missing essential information from another page?

Classify:

```text
SUFFICIENT
PARTIALLY_SUFFICIENT
INSUFFICIENT
CORRUPTED
```

Examples of insufficient blocks:

```text
“Arup said—how many bones...”
```

when the continuation is missing.

Or:

```text
“Using the figure below...”
```

when the figure is absent.

Or:

```text
“From the above table...”
```

when the table is not included.

These must not become standalone grounding chunks.

---

# 20. Context Expansion Before Rejection

When a block is insufficient, first attempt deterministic expansion:

```text
current block
+
previous block
+
next block
```

If this resolves the reference, merge the necessary content.

If it remains incomplete:

```text
REJECT
```

Do not ask an LLM to invent missing context.

---

# 21. Grounding Chunk Construction

Only after structure and sufficiency validation should chunks be produced.

Ideal chunk:

```text
one coherent educational unit
```

not:

```text
arbitrary 1,000-character window
```

Chunks may span pages.

Each chunk must retain:

```text
chunk_id
book_id
subject
grade
chapter
section
page_start
page_end
source_text
quality
```

---

# 22. Chunk Overlap

Use controlled overlap where necessary for continuity.

Do not duplicate entire pages excessively.

Recommended:

```text
small semantic overlap only when needed
```

Avoid creating hundreds of nearly identical chunks.

---

# 23. Source Quality Labels

Each chunk gets:

```text
HIGH
MEDIUM
LOW
REJECT
```

Suggested policy:

### HIGH

Clear OCR, complete context, valid structure.

### MEDIUM

Minor OCR uncertainty but meaning is recoverable deterministically.

### LOW

Readable but important uncertainty remains.

### REJECT

Corrupted, incomplete, missing dependencies, or semantically ambiguous.

Only HIGH should enter the first SFT-generation pilot.

MEDIUM may be kept for later manual review.

---

# 24. Do Not LLM-Repair OCR During Extraction

This is a hard rule.

The extraction pipeline may:

- normalize Unicode
- merge OCR lines
- restore reading order
- join cross-page paragraphs
- remove page furniture

It must NOT use an LLM to creatively rewrite damaged text.

If:

```text
OCR = “বীজগাদিডিকগরতিযা”
```

do not automatically turn it into:

```text
বীজগাণিতিক রাশি
```

unless a deterministic source/layout rule establishes that correction.

The original OCR must remain preserved regardless.

---

# 25. Extraction Audit Dataset

Produce an audit file:

```text
extraction_summary.json
```

with:

```text
books_processed
pages_processed
pages_high_quality
pages_review
pages_failed
blocks_created
blocks_rejected
chunks_created
chunks_rejected
ocr_error_rate_estimate
cross_page_merges
math_pages
science_pages
```

Also preserve rejection reasons.

Example:

```json
{
  "chunk_id": "...",
  "status": "REJECT",
  "reason": "INSUFFICIENT_CROSS_PAGE_CONTEXT"
}
```

---

# 26. Extraction Pilot

Do NOT process the entire WBBSE corpus first.

Start with a pilot:

```text
2–3 books
+
multiple subjects
+
different scan qualities
+
different grade levels
```

Recommended:

```text
one Mathematics book
one Science book
one Bengali/Literature book
```

Run them completely through OCR → reconstruction → chunking.

Then inspect:

- raw images
- raw OCR
- normalized OCR
- reconstructed blocks
- final chunks

Only after the extraction quality is acceptable should the full corpus run.

---

# 27. Human Review of Extraction

For the extraction pilot, manually inspect at least:

```text
20 random pages per book
```

plus:

```text
all low-confidence pages
all structural failures
all math-heavy pages
all table-heavy pages
all diagram-heavy pages
```

Check:

1. Bengali text accuracy
2. page order
3. paragraph boundaries
4. headings
5. mathematical symbols
6. questions
7. tables
8. cross-page continuity

---

# 28. Extraction Acceptance Criteria

Before full extraction:

```text
100% books discovered correctly
100% page numbering traceable
0 silently dropped pages
0 silently dropped OCR failures
0 corrupted chunk accepted as HIGH
0 missing cross-page continuity in reviewed sample
0 subject/grade metadata contradictions
0 obvious OCR garbage in HIGH chunks
```

Target:

```text
HIGH-quality chunks should be the dominant output.
```

Do not optimize for maximum chunk count.

Optimize for **maximum trustworthy chunk count**.

---

# 29. Final Extraction Output

The main grounding file should be:

```text
datasets/extraction/source_chunks/wbbse_grounding_chunks_v2.jsonl
```

Each line should contain:

```json
{
  "chunk_id": "...",
  "book_id": "...",
  "subject": "Science",
  "grade": 8,
  "chapter": "...",
  "section": "...",
  "topic": "...",
  "page_start": 45,
  "page_end": 46,
  "source_text": "...",
  "source_quality": "HIGH"
}
```

This file becomes the sole textbook grounding source for the next SFT regeneration stage.

---

# 30. Do Not Regenerate SFT Yet

After extraction, stop.

First run:

```text
extraction QA
→ metadata QA
→ source sufficiency QA
→ manual pilot review
```

Only after the extracted corpus passes should the SFT generation pipeline consume it.

The final architecture is:

```text
DOWNLOADED WBBSE BOOKS
        ↓
BOOK INVENTORY
        ↓
PAGE RENDERING
        ↓
EASYOCR
        ↓
OCR QUALITY CONTROL
        ↓
UNICODE NORMALIZATION
        ↓
LAYOUT / READING ORDER
        ↓
CROSS-PAGE RECONSTRUCTION
        ↓
STRUCTURAL SEGMENTATION
        ↓
CANONICAL METADATA
        ↓
SOURCE SUFFICIENCY
        ↓
HIGH-CONFIDENCE GROUNDING CHUNKS
        ↓
[STOP + REVIEW]
        ↓
ONLY THEN
        ↓
SFT TASK GENERATION
```

# 31. Non-Negotiable Principle

The extraction pipeline must optimize for:

> **faithful recovery of what the textbook actually says, not plausible reconstruction of what the textbook might have said.**

A missing fact is acceptable.

A hallucinated fact in the grounding corpus is not.

---

# 32. Recommended implementation files

Create:

```text
scratch/
├── inventory_wbbse_books.py
├── render_book_pages.py
├── run_easyocr_extraction.py
├── normalize_ocr.py
├── reconstruct_layout.py
├── reconstruct_cross_page_context.py
├── segment_textbook_structure.py
├── validate_source_chunks.py
├── build_grounding_chunks.py
└── audit_extraction.py
```

The final downstream SFT generator must consume only:

```text
wbbse_grounding_chunks_v2.jsonl
```

and never the raw OCR output directly.
