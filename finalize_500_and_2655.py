# -*- coding: utf-8 -*-
import json
from pathlib import Path

exp_file = Path('datasets/separated_datasets/batch_500_expansion/sft_500_expansion.jsonl')
records = []
with open(exp_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            records.append(json.loads(line))

print(f'Total 500 Expansion Records: {len(records)}')

clean_500 = []
for i, r in enumerate(records):
    msgs = r['messages']
    assert len(msgs) == 3, f'Record {i} does not have 3 messages'
    clean_500.append({'messages': msgs})

with open(exp_file, 'w', encoding='utf-8') as f:
    for r in clean_500:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')

out_dir = Path('datasets/separated_datasets/batch_500_expansion')
out_dir.mkdir(parents=True, exist_ok=True)

# 1. Part A (200 records)
part_a = clean_500[:200]
part_a_file = out_dir / 'part_a_pedagogy_200.jsonl'
with open(part_a_file, 'w', encoding='utf-8') as f:
    for r in part_a:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
print(f'Part A Pedagogy: {len(part_a)} records saved to {part_a_file}')

# 2. Part B (200 records)
part_b = clean_500[200:400]
part_b_file = out_dir / 'part_b_all_grades_curriculum_papers_200.jsonl'
with open(part_b_file, 'w', encoding='utf-8') as f:
    for r in part_b:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
print(f'Part B Curriculum Papers: {len(part_b)} records saved to {part_b_file}')

# 3. Part C (100 records)
part_c = clean_500[400:500]
part_c_file = out_dir / 'part_c_historic_naturalised_papers_100.jsonl'
with open(part_c_file, 'w', encoding='utf-8') as f:
    for r in part_c:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
print(f'Part C Historic Naturalised Papers: {len(part_c)} records saved to {part_c_file}')

# 4. Master 2,655 Merge
base_file = Path('datasets/sft_2155_combined_chatml.jsonl')
base_records = []
with open(base_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            base_records.append(json.loads(line))

print(f'Base records loaded: {len(base_records)}')

master_2655 = [{'messages': r['messages']} for r in (base_records + clean_500)]
print(f'Total Master Dataset records: {len(master_2655)}')

comb_dir = Path('datasets/separated_datasets/combined_2655')
comb_dir.mkdir(parents=True, exist_ok=True)

master_master_file = Path('datasets/gold_standard_sft_2655_master.jsonl')
chatml_file = comb_dir / 'sft_chatml_2655.jsonl'
sharegpt_file = comb_dir / 'sft_sharegpt_2655.json'
alpaca_file = comb_dir / 'sft_exact_3field_2655.jsonl'

# Export Master ChatML
with open(master_master_file, 'w', encoding='utf-8') as f:
    for r in master_2655:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')

with open(chatml_file, 'w', encoding='utf-8') as f:
    for r in master_2655:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')

# Export ShareGPT format
sharegpt_list = []
for i, r in enumerate(master_2655):
    convs = []
    for m in r['messages']:
        from_role = 'system' if m['role'] == 'system' else ('human' if m['role'] == 'user' else 'gpt')
        convs.append({'from': from_role, 'value': m['content']})
    sharegpt_list.append({'id': f'sahayak_sft_{i+1:05d}', 'conversations': convs})

with open(sharegpt_file, 'w', encoding='utf-8') as f:
    json.dump(sharegpt_list, f, ensure_ascii=False, indent=2)

# Export Exact 3-Field (Alpaca) format
with open(alpaca_file, 'w', encoding='utf-8') as f:
    for r in master_2655:
        f.write(json.dumps({
            'instruction': r['messages'][0]['content'],
            'input': r['messages'][1]['content'],
            'output': r['messages'][2]['content']
        }, ensure_ascii=False) + '\n')

print('ALL 2,655 EXPORTS COMPLETED SUCCESSFULLY!')
