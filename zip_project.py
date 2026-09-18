import os
import zipfile

project_dir = r"C:\Users\HP\.gemini\antigravity\scratch\SyntheticTutor"
downloads_zip = os.path.expanduser(r"~\Downloads\SyntheticTutor_Source_Code.zip")
desktop_zip = os.path.expanduser(r"~\Desktop\SyntheticTutor_Source_Code.zip")

print("Zipping SyntheticTutor project codebase...")

with zipfile.ZipFile(downloads_zip, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(project_dir):
        # Exclude .venv and large generated output dataset files from zip for fast packaging
        if ".venv" in root or "__pycache__" in root:
            continue
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_dir)
            zf.write(file_path, rel_path)

import shutil
shutil.copyfile(downloads_zip, desktop_zip)

print(f"Project ZIP created successfully!")
print(f"Downloads: {downloads_zip} ({os.path.getsize(downloads_zip)/(1024*1024):.2f} MB)")
print(f"Desktop: {desktop_zip}")
