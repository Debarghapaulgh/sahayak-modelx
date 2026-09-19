# Provenance audit — SFT sets (2026-09-19)

Classification is by **file lineage** because no record carries provenance fields. API-generated records are quarantined until the licence decision (#21). Regenerate: `python DataEngine/provenance/audit_provenance.py`.

| File | Generator | Provider(s) | Status | Records | Unique | Dup. of earlier file | With provenance keys | Parse |
|---|---|---|---|---:|---:|---:|---:|---|
| Final/gold_standard_sft_2000_api.jsonl | API generation (gold standard) | OpenAI / Gemini | QUARANTINE | 2000 | 2000 | 0 | 0 | ok |
| Final/sft_500_expansion.jsonl | generate_500_specialized_sft.py | Sarvam, Gemini, Groq | QUARANTINE | 500 | 500 | 0 | 0 | ok |
| Final/sft_155_additional_chatml.jsonl | unknown | unknown | QUARANTINE | 155 | 155 | 0 | 0 | ok |
| Final/part1_sft_best_records_curated.jsonl | Part-1 pipeline (docs/FINAL_DATASET_CREATION_PART1_SPECIFICATION.md) | OpenAI / Gemini via synthetictutor.llm | QUARANTINE | 164 | 164 | 0 | 0 | ok |
| Final/part1_good_records_unique_57.jsonl | Part-1 pipeline (docs/FINAL_DATASET_CREATION_PART1_SPECIFICATION.md) | OpenAI / Gemini via synthetictutor.llm | QUARANTINE | 57 | 57 | 0 | 0 | ok |
| Final/part1_additional_salvage_new_passable_100.jsonl | Part-1 pipeline (docs/FINAL_DATASET_CREATION_PART1_SPECIFICATION.md) | OpenAI / Gemini via synthetictutor.llm | QUARANTINE | 100 | 100 | 0 | 0 | ok |
| Final/part1_strict_good_records_45 (1).jsonl | Part-1 pipeline (docs/FINAL_DATASET_CREATION_PART1_SPECIFICATION.md) | OpenAI / Gemini via synthetictutor.llm | QUARANTINE | 45 | 45 | 21 | 0 | ok |
| Final/final_merged_dataset.jsonl | merge of the files above | mixed | QUARANTINE (derived) | 3000 | 3000 | 648 | 0 | ok |
| Finetune/data/train_v3.jsonl | Finetune/prepare_data.py: teacher-checked templates | own | USABLE | 491 | 475 | 0 | 0 | ok |
| Finetune/data/eval_real.jsonl | Finetune/prepare_data.py: held-out, 0 template overlap | own | USABLE (held-out) | 66 | 66 | 0 | 0 | ok |

**Usable now (own, teacher-checked): 541 unique records.**
**Quarantined (API-generated / derived / unknown): 5352 unique records.**

## Required before any quarantined record can train
1. Licence decision per provider (OpenAI, Gemini, Groq, Sarvam, OpenRouter models) — #21.
2. Provenance field on every record: `{generator_model, provider, licence, chunk_ids, locale_keys, validator_version, teacher_id?}` — #20 item 7.
3. Teacher review to `approved` — #17.
