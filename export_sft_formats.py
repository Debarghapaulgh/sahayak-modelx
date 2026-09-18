"""
Export Part 1 SFT Dataset to Training-Ready SFT Formats:
1. OpenAI / ChatML Messages Format (part1_sft_train_1500.jsonl)
2. ShareGPT Format (part1_sharegpt_1500.jsonl)
3. Task-specific ChatML splits
"""

import os
import json

def get_system_prompt(board: str, grade: int, subject: str, topic: str) -> str:
    board_full = {
        "WBBPE": "পশ্চিমবঙ্গ প্রাথমিক শিক্ষা পর্ষদ (WBBPE)",
        "WBBSE": "পশ্চিমবঙ্গ মধ্যশিক্ষা পর্ষদ (WBBSE)",
        "WBCHSE": "পশ্চিমবঙ্গ উচ্চমাধ্যমিক শিক্ষা সংসদ (WBCHSE)"
    }.get(board, "পশ্চিমবঙ্গ মধ্যশিক্ষা পর্ষদ (WBBSE)")

    grade_bengali = {
        1: "প্রথম শ্রেণি", 2: "দ্বিতীয় শ্রেণি", 3: "তৃতীয় শ্রেণি", 4: "চতুর্থ শ্রেণি",
        5: "পঞ্চম শ্রেণি", 6: "ষষ্ঠ শ্রেণি", 7: "সপ্তম শ্রেণি", 8: "অষ্টম শ্রেণি",
        9: "নবম শ্রেণি", 10: "দশম শ্রেণি", 11: "একাদশ শ্রেণি", 12: "দ্বাদশ শ্রেণি"
    }.get(grade, f"{grade}ম শ্রেণি")

    return f"""তুমি 'সহায়ক এআই' (SahayakAI) — {board_full} বেঙ্গলি-মিডিয়াম স্কুলের শিক্ষার্থী ও শিক্ষক মহাশয়দের জন্য তৈরি একজন অভিজ্ঞ, বিশেষায়িত অ্যাকাডেমিক AI টিউটর। তোমার কাজ হলো পাঠ্যক্রম অনুযায়ী সহজ, সাবলীল, সঠিক ও শিক্ষার্থী-উপযোগী বাংলা ভাষায় পাঠদান, ধারণা ব্যাখ্যা, সমস্যা সমাধান এবং অধ্যয়ন-সংক্রান্ত সহায়তা প্রদান করা।

নিয়মাবলী ও সম্বোধন:
১. শিক্ষক বা অভিভাবকের উদ্দেশ্যে সম্মানসূচক 'আপনি' ভাষা ব্যবহার করবে।
২. শিক্ষার্থীর উদ্দেশ্যে সহজ, বন্ধুভাবাপন্ন 'তুমি/তোমরা' ভাষা ব্যবহার করবে।
৩. স্পষ্ট, প্রাঞ্জল ও স্বাভাবিক ভাষায় সরাসরি শিক্ষামূলক উত্তরে প্রবেশ করবে; অপ্রয়োজনীয় অভিবাদন, প্রশংসা বা motivational filler এড়িয়ে চলবে।
৪. পাঠ্যক্রম-উপযোগী প্রমিত বাংলা পরিভাষা ব্যবহার করবে।
৫. সাধারণ বাংলা গদ্যে সব সংখ্যা বাংলা অঙ্কে লিখবে: ০, ১, ২, ৩, ৪, ৫, ৬, ৭, ৮, ৯।
৬. বৈধ mathematical/scientific notation যেমন x², x^2, H₂O, CO₂, a₁, ∠ABC বা অনুরূপ notation বিকৃত করবে না।

শিক্ষাদান ও পাঠ্যক্রম-নির্ভরতা:
৭. পাঠ্যক্রম ও বিষয়বস্তুর ধারণা সঠিকভাবে ব্যাখ্যা করবে এবং কোনো বিভ্রান্তিকর তথ্য প্রদান করবে না।
৮. সাধারণ বাংলা গদ্যে 'প্রদত্ত পাঠ্যাংশে' বা 'উক্ত পাঠ্যাংশ অনুসারে' জাতীয় কৃত্রিম বাক্য পরিহার করে সরাসরি বিষয়ের ধারণা সহজভাবে বুঝিয়ে দেবে।
৯. গণিত ও বিজ্ঞানের ক্ষেত্রে সূত্র, হিসাব, একক এবং intermediate steps সঠিক রাখবে।
১০. উত্তর সম্পূর্ণ রাখবে এবং যথাযথ বিরামচিহ্ন (। বা ?) দিয়ে শেষ করবে।

সহায়ক এআই (SahayakAI) পাঠ্যসূচি বিবরণী:
- পর্ষদ/সংসদ: {board_full}
- বিষয়: {subject}
- শ্রেণি: {grade_bengali}
- বিষয়বস্তু: {topic}
- অঞ্চল/জেলা: পশ্চিমবঙ্গ সাধারণ পাঠ্যক্রম"""

def export_sft_formats():
    base_dir = "datasets/textbook_sft_part1"
    
    files = [
        ("QA", os.path.join(base_dir, "qa_final.jsonl"), os.path.join(base_dir, "part1_sft_qa_800.jsonl")),
        ("LESSON_PLAN", os.path.join(base_dir, "lesson_plan_final.jsonl"), os.path.join(base_dir, "part1_sft_lesson_plan_350.jsonl")),
        ("QUIZ", os.path.join(base_dir, "quiz_final.jsonl"), os.path.join(base_dir, "part1_sft_quiz_350.jsonl"))
    ]

    all_chatml_records = []
    all_sharegpt_records = []

    for task_name, in_path, out_chatml_path in files:
        task_chatml = []
        with open(in_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                
                board = r.get("curriculum", {}).get("board", "WBBSE")
                grade = r.get("curriculum", {}).get("grade", 8)
                subject = r.get("curriculum", {}).get("subject", "Bengali")
                topic = r.get("curriculum", {}).get("topic", "সাধারণ পাঠ")
                
                sys_prompt = get_system_prompt(board, grade, subject, topic)
                user_prompt = r.get("user_prompt")
                assistant_response = r.get("assistant_response")

                chatml_entry = {
                    "messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": assistant_response}
                    ]
                }
                
                sharegpt_entry = {
                    "id": r.get("id"),
                    "conversations": [
                        {"from": "system", "value": sys_prompt},
                        {"from": "human", "value": user_prompt},
                        {"from": "gpt", "value": assistant_response}
                    ]
                }

                task_chatml.append(chatml_entry)
                all_chatml_records.append(chatml_entry)
                all_sharegpt_records.append(sharegpt_entry)

        with open(out_chatml_path, "w", encoding="utf-8") as out_f:
            for item in task_chatml:
                out_f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"Exported {len(task_chatml)} {task_name} records to {out_chatml_path}")

    # Export consolidated 1,500 SFT files
    master_chatml_path = os.path.join(base_dir, "part1_sft_train_1500.jsonl")
    with open(master_chatml_path, "w", encoding="utf-8") as f:
        for item in all_chatml_records:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"\nSuccessfully created Master ChatML SFT file: {master_chatml_path} ({len(all_chatml_records)} rows)")

    master_sharegpt_path = os.path.join(base_dir, "part1_sharegpt_1500.jsonl")
    with open(master_sharegpt_path, "w", encoding="utf-8") as f:
        for item in all_sharegpt_records:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Successfully created Master ShareGPT SFT file: {master_sharegpt_path} ({len(all_sharegpt_records)} rows)")

if __name__ == "__main__":
    export_sft_formats()