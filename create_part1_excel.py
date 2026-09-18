"""
Create Consolidated Part 1 SFT Excel Master.
Builds SahayakAI_Part1_SFT_1500_Master.xlsx with full formatting and sheets.
"""

import os
import json
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def build_part1_excel():
    base_dir = "datasets/textbook_sft_part1"
    
    files = {
        "QA_800": os.path.join(base_dir, "qa_final.jsonl"),
        "Lesson_Plans_350": os.path.join(base_dir, "lesson_plan_final.jsonl"),
        "Quizzes_350": os.path.join(base_dir, "quiz_final.jsonl")
    }
    
    excel_path = "SahayakAI_Part1_SFT_1500_Master.xlsx"
    excel_path_mirror = os.path.join(base_dir, "SahayakAI_Part1_SFT_1500_Master.xlsx")
    
    dfs = {}
    for sheet_name, fpath in files.items():
        rows = []
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        r = json.loads(line)
                        rows.append({
                            "ID": r.get("id"),
                            "Task Type": r.get("task_type"),
                            "Requester": r.get("requester_role"),
                            "Target": r.get("instructional_target"),
                            "Board": r.get("curriculum", {}).get("board"),
                            "Stage": r.get("curriculum", {}).get("stage"),
                            "Grade": r.get("curriculum", {}).get("grade"),
                            "Subject": r.get("curriculum", {}).get("subject"),
                            "Textbook": r.get("curriculum", {}).get("textbook"),
                            "Chapter": r.get("curriculum", {}).get("chapter"),
                            "Topic": r.get("curriculum", {}).get("topic"),
                            "User Prompt": r.get("user_prompt"),
                            "Assistant Response": r.get("assistant_response"),
                            "Validation Status": "APPROVED" if r.get("validation", {}).get("overall_passed") else "REVIEW"
                        })
        dfs[sheet_name] = pd.DataFrame(rows)
        print(f"Loaded {len(rows)} rows for sheet {sheet_name}")

    for out_f in [excel_path, excel_path_mirror]:
        with pd.ExcelWriter(out_f, engine="openpyxl") as writer:
            for sheet_name, df in dfs.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
        # Style workbook
        wb = openpyxl.load_workbook(out_f)
        header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        regular_font = Font(name="Calibri", size=10)
        thin_border = Border(
            left=Side(style="thin", color="D9D9D9"),
            right=Side(style="thin", color="D9D9D9"),
            top=Side(style="thin", color="D9D9D9"),
            bottom=Side(style="thin", color="D9D9D9")
        )

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            ws.views.sheetView[0].showGridLines = True
            
            # Header styling
            for col in range(1, ws.max_column + 1):
                cell = ws.cell(row=1, column=col)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws.row_dimensions[1].height = 28

            # Auto width & row styling
            for col in ws.columns:
                header_val = str(col[0].value)
                col_letter = get_column_letter(col[0].column)
                if "Response" in header_val:
                    ws.column_dimensions[col_letter].width = 60
                elif "Prompt" in header_val:
                    ws.column_dimensions[col_letter].width = 40
                elif "Topic" in header_val or "Textbook" in header_val:
                    ws.column_dimensions[col_letter].width = 25
                else:
                    ws.column_dimensions[col_letter].width = 14

        wb.save(out_f)
        print(f"Successfully saved styled master Excel: {out_f}")

if __name__ == "__main__":
    build_part1_excel()