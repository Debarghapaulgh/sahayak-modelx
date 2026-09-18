import os
import zipfile
from pathlib import Path

def create_zip():
    base_dir = Path("e:/Downloads/SyntheticTutor")
    repo_dir = base_dir / "northbengal-dataset-forge-2026-08-19" / "northbengal-dataset-forge"
    out_zip = base_dir / "WBBSE_Extracted_Textbooks_and_Dataset.zip"
    
    print(f"Creating ZIP archive: {out_zip}")
    
    items_to_zip = [
        repo_dir / "raw-textbooks" / "wbbse",
        repo_dir / "forge" / "config" / "wbbse_topics",
        repo_dir / "datasets" / "seed" / "wbbse",
        repo_dir / "TEXTBOOK_EXTRACTION_PROCESS.md",
        repo_dir / "forge" / ".cache" / "chunk_registry.json"
    ]
    
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in items_to_zip:
            if not item.exists():
                print(f"Skipping non-existent path: {item}")
                continue
            if item.is_file():
                arcname = item.relative_to(repo_dir)
                zf.write(item, arcname)
                print(f"Added file: {arcname}")
            elif item.is_dir():
                for root, _, files in os.walk(item):
                    for f in files:
                        fp = Path(root) / f
                        arcname = fp.relative_to(repo_dir)
                        zf.write(fp, arcname)
                print(f"Added directory: {item.relative_to(repo_dir)}")
                
    size_mb = os.path.getsize(out_zip) / (1024 * 1024)
    print(f"ZIP creation complete! Archive Size: {size_mb:.2f} MB")

if __name__ == "__main__":
    create_zip()
