import os
import shutil
from pathlib import Path

def organize_pdfs():
    base_dir = Path("e:/Downloads/SyntheticTutor")
    target_dir = base_dir / "WBBSE_Books_PDFs_By_Class"
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"Organizing PDF files into: {target_dir}")

    # Search for all PDF files under SyntheticTutor
    pdf_files = list(base_dir.rglob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files total.")

    copied_count = 0
    for pdf_path in pdf_files:
        # Determine class from parent path structure
        parts = [p.lower() for p in pdf_path.parts]
        class_folder = "Other_PDFs"

        for part in parts:
            if "class 10" in part or "class_10" in part:
                class_folder = "Class_10"
                break
            elif "class 12" in part or "class_12" in part:
                class_folder = "Class_12"
                break
            elif "class 8" in part or "class_8" in part:
                class_folder = "Class_8"
                break
            elif "class 7" in part or "class_7" in part:
                class_folder = "Class_7"
                break
            elif "class 5" in part or "class_5" in part:
                class_folder = "Class_5"
                break
            elif "class 4" in part or "class_4" in part:
                class_folder = "Class_4"
                break
            elif "class 3" in part or "class_3" in part:
                class_folder = "Class_3"
                break
            elif "class 6" in part or "class_6" in part:
                class_folder = "Class_6"
                break
            elif "class 9" in part or "class_9" in part:
                class_folder = "Class_9"
                break

        dest_class_dir = target_dir / class_folder
        dest_class_dir.mkdir(parents=True, exist_ok=True)

        dest_file = dest_class_dir / pdf_path.name
        shutil.copy2(pdf_path, dest_file)
        copied_count += 1

    print(f"Successfully organized {copied_count} PDF files into class subfolders!")

if __name__ == "__main__":
    organize_pdfs()
