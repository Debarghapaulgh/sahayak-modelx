# Teacher validation — how approval is recorded (Track 6, #17)

Teachers have **already validated content informally**. They are not tech-savvy and will not use GitHub,
YAML or spreadsheets. So the rule is: **teachers judge; the team records.**

## Principle
- The teacher's word is the authority. The team's only job is to capture it faithfully, with **who / when /
  how**, so a record can move to `approved`.
- Nothing in this process may require a teacher to open a link, a form, or a file.

## Channels (use whatever the teacher already uses)
1. **In person** — printed A4 review sheet in Bengali; tick / cross / note per item; the team photographs the sheet.
2. **WhatsApp** — the same sheet as an image or PDF; the teacher replies with ticks in a message or a voice note.
3. **Phone call** — a team member reads the items; the teacher answers; the team fills the sheet.

## The review sheet
Generated from the store (`DataEngine/localization/data/*.yaml`; SFT batches) by `DataEngine/localization/make_review_sheet.py`
(`python make_review_sheet.py`, defaults to West Bengal zones and pending items): **≤ 20 items per sheet, Bengali only**. Each item shows the local example or the answer exactly as a
student would see it, then three boxes — **ঠিক আছে · ভুল · বদলাতে হবে** — and a line for the teacher's note.
Sheet id and item ids are printed small so results can be keyed back without ambiguity.

## Recording (a team member, the same day)
- **Ontology records:** `validation.authenticity: {validated_by: T-<initials>, date: YYYY-MM-DD,
  method: print | whatsapp | call | in_person, sheet: <id>, note: "<teacher's words>"}` and
  `status: approved` (or `rejected` with the reason). `pedagogy` and `factual` stay team-checked.
- **SFT records:** provenance gains `teacher_id`, `validated_on`, `method`, `sheet_id`.
- The photo / screenshot / voice note is kept as evidence, **outside git**, named by sheet id.

## Retroactive ledger — the informal approvals already given
Fill this first. It turns approvals that already happened into `approved` status with a name on them.

| Teacher (initials) | School / district | Grades × subjects | What they validated | When | Evidence held? |
|---|---|---|---|---|---|
| _fill_ | | | e.g. `Finetune/data` templates (491 train / 66 eval) | 2026-0? | photo / message / memory |
| _fill_ | | | e.g. local entities: mango, dhak, dahi (north_bengal_tea_belt) | | |

## Consent and privacy
Teacher names go into provenance only with their consent; otherwise initials + a school code.
No student data on any sheet (DPDP §9).
