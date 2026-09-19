#!/usr/bin/env python3
"""Bengali A4 review sheets for teacher validation (Track 6, #17). Teachers judge; the team records.

Reads the store (data/*.yaml), selects items that still need a teacher's word (default: West Bengal
zones, not yet approved), and renders sheets of <= 20 items with three tick boxes each. Sheet and item
ids are printed so verdicts can be keyed back into the store without ambiguity.

    python make_review_sheet.py                 # WB zones, pending items -> review_sheets/RS-<date>-01.pdf
    python make_review_sheet.py --all-zones --include-approved --batch 15
"""
import argparse
import datetime
import html
import pathlib
import subprocess

import yaml

HERE = pathlib.Path(__file__).parent
WB_ZONES = {"north_bengal_tea_belt", "north_bengal", "sundarbans_delta", "gangetic_plain",
            "rarh_plateau", "kolkata_metro", "medinipur_coastal"}
BN = {  # display names for seed ids; extend as the store grows (unknown ids fall back to the id)
    "c_gravity": "মহাকর্ষ (অভিকর্ষ বল)", "c_photo": "সালোকসংশ্লেষ", "c_acidbase": "অ্যাসিড, ক্ষার ও নির্দেশক",
    "c_microbe": "উপকারী অণুজীব", "c_evap": "বাষ্পীভবন ও অবস্থার পরিবর্তন", "c_friction": "ঘর্ষণ",
    "c_sound": "শব্দ ও কম্পন", "c_reflect": "আলোর প্রতিফলন",
    "mango": "আম", "khichdi": "খিচুড়ি", "dahi_curd": "দই", "haldi_turmeric": "হলুদ", "dhak_drum": "ঢাক",
    "coconut": "নারকেল", "matka": "মাটির কলসি", "solar_salt_pan": "লবণের খেত", "temple_tank": "মন্দিরের পুকুর",
    "north_bengal_tea_belt": "উত্তরবঙ্গ (চা-বলয়)", "sundarbans_delta": "সুন্দরবন",
    "fruit": "ফল", "crop": "ফসল", "food": "খাবার", "festival": "উৎসব", "occupation": "পেশা", "animal": "প্রাণী",
    "landmark": "স্থান", "tool": "সরঞ্জাম", "weather": "আবহাওয়া", "dish": "রান্না",
}
STRATEGY_BN = {"anchor_substitution": "স্থানীয় উদাহরণ", "analogy": "উপমা", "applied_context": "প্রয়োগ",
               "cultural_grounding": "সাংস্কৃতিক", "sensory": "অনুভব"}
Q_SUB = "এই উদাহরণটি কি আপনার এলাকার ছাত্রছাত্রীদের কাছে পরিচিত, এবং এই ধারণাটি পড়ানোর জন্য উপযুক্ত?"
Q_ENT = "এটি কি আপনার এলাকায় সাধারণভাবে দেখা যায় বা ব্যবহৃত হয়?"


def bn(key):
    return BN.get(key, str(key).replace("_", " "))


def load_items(zones, include_approved):
    ents = yaml.safe_load((HERE / "data" / "local-entities.seed.yaml").read_text())
    subs = yaml.safe_load((HERE / "data" / "substitutions.seed.yaml").read_text())
    concepts = {c["id"]: c for c in subs.get("concepts", [])}
    items = []
    for s in subs.get("substitutions", []):
        if zones and s.get("zone_id") not in zones:
            continue
        if not include_approved and s.get("status") == "approved":
            continue
        c = concepts.get(s["concept_id"], {})
        ent = s.get("local_anchor", {}).get("entity_id", "")
        items.append({
            "id": s["id"], "kind": "substitution",
            "title": f'{bn(c.get("id", s["concept_id"]))} — {bn(ent)} ({STRATEGY_BN.get(s.get("strategy"), s.get("strategy"))})',
            "meta": f'শ্রেণি {c.get("grade", "?")} · অঞ্চল: {bn(s.get("zone_id", ""))}',
            "question": Q_SUB,
            "draft": (s.get("generated_text") or "").strip(),
            "flags": s.get("disanalogy_flags") or [],
        })
    for e in ents.get("entities", []):
        if zones and not (set(e.get("zones", [])) & zones):
            continue
        validated = (e.get("authenticity") or {}).get("validated_by", "pending_teacher")
        if not include_approved and validated != "pending_teacher":
            continue
        items.append({
            "id": e["id"], "kind": "entity",
            "title": f'{bn(e["id"])} ({bn(e.get("kind", ""))})',
            "meta": "অঞ্চল: " + ", ".join(bn(z) for z in e.get("zones", []) if not zones or z in zones),
            "question": Q_ENT,
            "draft": (e.get("authenticity") or {}).get("note", ""),
            "flags": [],
        })
    return items


CSS = """
@page { size: A4; margin: 16mm 16mm 18mm 16mm;
  @bottom-left { content: "SahayakAI · শিক্ষক পর্যালোচনা · টিম পূরণ করবে: T-______  তারিখ ______  মাধ্যম: ছাপা / হোয়াটসঅ্যাপ / ফোন";
                 font: 400 7.5pt "Kohinoor Bangla", Inter, sans-serif; color: #6b7278; }
  @bottom-right { content: counter(page) " / " counter(pages); font: 400 8pt "PT Mono", Menlo, monospace; color: #6b7278; } }
body { font-family: "Kohinoor Bangla", "Source Serif 4", serif; font-size: 11pt; line-height: 1.55; color: #16191c; margin: 0; }
.hd { display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1.2pt solid #16191c; padding-bottom: 3mm; margin-bottom: 4mm; }
.hd h1 { font-size: 17pt; margin: 0; font-weight: 700; }
.hd .id { font: 600 9pt "PT Mono", Menlo, monospace; color: #0d5b56; text-align: right; }
.who { display: flex; gap: 8mm; font-size: 10.5pt; margin: 0 0 4mm; }
.who span { flex: 1; border-bottom: .6pt solid #9aa1a6; padding-bottom: 1mm; }
.how { background: #f2f6f4; border-left: 2.5pt solid #0d5b56; padding: 2.5mm 4mm; font-size: 10pt; margin: 0 0 5mm; }
.item { break-inside: avoid; border: .6pt solid #d7d9d2; border-radius: 2mm; padding: 3mm 4mm 3.5mm; margin: 0 0 3.5mm; }
.item .n { display: inline-block; min-width: 7mm; font: 700 11pt Inter, sans-serif; color: #0d5b56; }
.item .t { font-weight: 700; font-size: 12pt; }
.item .m { font-size: 9pt; color: #6b7278; margin: .5mm 0 1.5mm 7mm; }
.item .q { margin: 0 0 2mm 7mm; }
.item .d { margin: 0 0 2mm 7mm; font-size: 9.6pt; color: #3c444a; background: #fbf9f2; border: .5pt solid #e6e0cf; padding: 2mm 3mm; border-radius: 1.5mm; }
.item .d b { color: #8a5510; font-weight: 600; }
.item .f { margin: 0 0 2mm 7mm; font-size: 9.2pt; color: #8a5510; }
.boxes { margin: 1mm 0 0 7mm; font-size: 11pt; }
.boxes span { display: inline-block; margin-right: 9mm; }
.box { display: inline-block; width: 5mm; height: 5mm; border: 1pt solid #16191c; vertical-align: -1mm; margin-right: 1.5mm; border-radius: .6mm; }
.note { margin: 2.5mm 0 0 7mm; font-size: 9.5pt; color: #6b7278; }
.note .line { display: inline-block; width: 128mm; border-bottom: .6pt solid #9aa1a6; vertical-align: -1mm; margin-left: 2mm; }
.ids { font: 400 7pt "PT Mono", Menlo, monospace; color: #9aa1a6; float: right; }
"""


def render(sheet_id, items, date):
    rows = []
    for i, it in enumerate(items, 1):
        draft = ""
        if it["draft"]:
            label = "খসড়া ব্যাখ্যা (ইংরেজি খসড়া; বাংলা সংস্করণ অনুমোদনের পরে):" if it["kind"] == "substitution" else "টীকা:"
            draft = f'<div class="d"><b>{label}</b> {html.escape(it["draft"])}</div>'
        flags = "".join(f'<div class="f">সতর্কতা: {html.escape(f)}</div>' for f in it["flags"])
        rows.append(f"""<div class="item"><span class="ids">{html.escape(it["id"])}</span>
<span class="n">{i}.</span><span class="t">{html.escape(it["title"])}</span>
<div class="m">{html.escape(it["meta"])}</div>
<div class="q">{it["question"]}</div>{draft}{flags}
<div class="boxes"><span><i class="box"></i>ঠিক আছে</span><span><i class="box"></i>ভুল</span><span><i class="box"></i>বদলাতে হবে</span></div>
<div class="note">আপনার মন্তব্য:<span class="line"></span></div></div>""")
    return f"""<!doctype html><html lang="bn"><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="hd"><h1>স্থানীয় উদাহরণ পর্যালোচনা</h1><div class="id">{sheet_id}<br>{date}</div></div>
<div class="who"><span>শিক্ষকের নাম: </span><span>বিদ্যালয় / জেলা: </span><span>শ্রেণি ও বিষয়: </span></div>
<div class="how">প্রতিটি উদাহরণ পড়ুন। যেটি আপনার এলাকার ছাত্রছাত্রীদের জন্য ঠিক, সেখানে <b>ঠিক আছে</b>-তে টিক দিন।
ভুল হলে <b>ভুল</b>, আর ঠিক করলে চলবে এমন হলে <b>বদলাতে হবে</b>-তে টিক দিয়ে এক লাইনে লিখুন কী বদলাবেন।
কোনো লিঙ্ক বা ফর্ম নেই — এই কাগজ বা এর ছবিই যথেষ্ট।</div>
{''.join(rows)}
</body></html>"""


def main():
    ap = argparse.ArgumentParser(description="Bengali teacher review sheets from the localisation store")
    ap.add_argument("--all-zones", action="store_true", help="include non-WB zones")
    ap.add_argument("--include-approved", action="store_true")
    ap.add_argument("--batch", type=int, default=20)
    ap.add_argument("--out", default=str(HERE / "review_sheets"))
    a = ap.parse_args()
    zones = None if a.all_zones else WB_ZONES
    items = load_items(zones, a.include_approved)
    if not items:
        print("nothing to review"); return
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    date = datetime.date.today().isoformat()
    for n in range(0, len(items), a.batch):
        sheet_id = f"RS-{date.replace('-', '')}-{n // a.batch + 1:02d}"
        htmlp = out / f"{sheet_id}.html"; pdfp = out / f"{sheet_id}.pdf"
        htmlp.write_text(render(sheet_id, items[n:n + a.batch], date), encoding="utf-8")
        r = subprocess.run(["weasyprint", "-e", "utf-8", str(htmlp), str(pdfp)], capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f"weasyprint failed for {sheet_id}: {r.stderr[:400]}")
        print(f"{sheet_id}: {len(items[n:n + a.batch])} items -> {pdfp}")


if __name__ == "__main__":
    main()
