#!/usr/bin/env python3
"""Compile the West Bengal localisation store into SFT data (Tracks 3/4, #21 #22). v2: scaled to ~10k.

Every record: Bengali, WB register (teacher = আপনি, student = তুমি), Bengali digits, format by task
(numbered steps ONLY in worked maths), the canonical exam term kept, provenance attached, licence "own".
Worked sums are computed programmatically, so every number in a solution is correct by construction.
Held-out split is by TEMPLATE (a template's instances are all-train or all-eval): 0 template overlap.
The teacher-checked Finetune/data sets (own licence) are folded in with their own provenance.

    python compile_wb_sft.py            -> ../out/sft_wb_v1_{train,eval}.jsonl + MANIFEST.json + sample_50.jsonl
"""
import argparse
import hashlib
import json
import pathlib
import random
import sys

import yaml

from gate import check, load_store

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent.parent
OUT = HERE.parent / "out"
BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
SYSTEM_BN = ("তুমি SahayakAI, পশ্চিমবঙ্গের সরকারি স্কুলের ছাত্রছাত্রী ও শিক্ষকদের জন্য বাংলা মাধ্যমের শিক্ষা-সহায়ক। "
             "গণনার প্রশ্নে ধাপে ধাপে দেখাও; অন্য সব ক্ষেত্রে সরাসরি, সংক্ষিপ্ত ও কাজের উপযোগী উত্তর দাও। সাধারণ তথ্যপ্রশ্নে "
             "ধাপ নম্বর দিও না। শিক্ষককে 'আপনি', ছাত্রছাত্রীকে 'তুমি'। সব সংখ্যা বাংলা অঙ্কে।")
CAP_PER_TEMPLATE = 380          # train instances per template variant
EVAL_CAP_PER_TEMPLATE = 40      # held-out: the last variant of every family with >= 2 variants (family-balanced eval)
TEMPLATE_RE = __import__("re").compile(r"^(.*)\.v(\d+)$")
KIDS = ["মিতু", "রাজু", "রিনা", "সুমন", "পিয়ালী", "বাবলু", "টুম্পা", "সোনালি", "পেমা", "আরিফ", "রেশমা", "গোপাল", "লক্ষ্মী", "সঞ্জয়", "নাসরিন", "বিমল"]
BANGLA_MONTHS = ["বৈশাখ", "জ্যৈষ্ঠ", "আষাঢ়", "শ্রাবণ", "ভাদ্র", "আশ্বিন", "কার্তিক", "অগ্রহায়ণ", "পৌষ", "মাঘ", "ফাল্গুন", "চৈত্র"]
DISTRICT_BN = {"Darjeeling": "দার্জিলিং", "Kalimpong": "কালিম্পং", "Jalpaiguri": "জলপাইগুড়ি", "Alipurduar": "আলিপুরদুয়ার", "Cooch Behar": "কোচবিহার",
               "Malda": "মালদহ", "Uttar Dinajpur": "উত্তর দিনাজপুর", "Dakshin Dinajpur": "দক্ষিণ দিনাজপুর", "Murshidabad": "মুর্শিদাবাদ", "Nadia": "নদিয়া",
               "Purba Bardhaman": "পূর্ব বর্ধমান", "Paschim Bardhaman": "পশ্চিম বর্ধমান", "Hooghly": "হুগলি", "Howrah": "হাওড়া", "North 24 Parganas": "উত্তর ২৪ পরগনা",
               "South 24 Parganas": "দক্ষিণ ২৪ পরগনা", "Kolkata": "কলকাতা", "Bankura": "বাঁকুড়া", "Purulia": "পুরুলিয়া", "Birbhum": "বীরভূম", "Jhargram": "ঝাড়গ্রাম",
               "Purba Medinipur": "পূর্ব মেদিনীপুর", "Paschim Medinipur": "পশ্চিম মেদিনীপুর"}


def district_bn(name):
    """'Howrah (rural)' -> 'হাওড়া'; unknown names fall back to the source string with Bengali digits."""
    base = name.split(" (")[0].strip()
    return DISTRICT_BN.get(base, bn(base))


def zname(z):
    """Zone name without a trailing 'অঞ্চল', so sentences can add their own 'অঞ্চলে'/'এলাকার'."""
    return (z.get("name_bn") or z["id"]).replace(" অঞ্চল", "").strip()


VOWEL_END = set("অআইঈউঊঋএঐওঔািীুূৃেৈোৌ")
SUBJECT_BN = {"Science": "বিজ্ঞান", "Mathematics": "গণিত", "Maths": "গণিত", "Math": "গণিত", "EVS": "পরিবেশ", "Physical Science": "ভৌতবিজ্ঞান", "Life Science": "জীবনবিজ্ঞান"}


def gen(w):
    """Genitive without a hyphen: চিংড়ি -> চিংড়ির, কয়লা -> কয়লার, গোপাল -> গোপালের, ইলিশ মাছ -> ইলিশ মাছের."""
    w = __import__("re").sub(r"\s*\(.*?\)\s*$", "", w.strip())
    last = w[-2] if w.endswith("ঁ") and len(w) > 1 else w[-1]
    return w + ("র" if last in VOWEL_END else "ের")


def rate_phrase(unit, p):
    return f"একটি {bn(p)} টাকা" if unit == "টি" else f"{bn(p)} টাকা {unit}"


def bn(x):
    """Render any number/str with Bengali digits."""
    if isinstance(x, float) and x.is_integer():
        x = int(x)
    return str(x).translate(BN_DIGITS)


def rec(task, target, user, assistant, prov, template):
    return {"messages": [{"role": "system", "content": SYSTEM_BN},
                         {"role": "user", "content": user},
                         {"role": "assistant", "content": assistant}],
            "task_family": task, "instructional_target": target, "template_id": template,
            "provenance": {"generator": "DataEngine/localization/compile_wb_sft.py", "source": "localisation store v1",
                           "licence": "own", "validated_by": "teacher_informal", "attested_by": "AG",
                           "date": "2026-09-19", **prov}}


def worked(steps, answer_line):
    return "\n".join(steps) + f"\n\nঅতএব নির্ণেয় উত্তর: {answer_line}"


def pick(rng, options, i):
    """Deterministic variant choice that also names the template variant."""
    k = i % len(options)
    return options[k], k


# ------------------------------------------------------------------ substitutions -> explanations
def from_substitutions(store, rng):
    out = []
    for sid, s in store["substitutions"].items():
        if s.get("status") != "approved" or not s.get("text_bn") or not check(s, store)["ok"]:
            continue
        c = store["concepts"][s["concept_id"]]; e = store["entities"][s["local_anchor"]["entity_id"]]; z = store["zones"][s["zone_id"]]
        prov = {"concept_id": c["id"], "entity_id": e["id"], "zone_id": z["id"], "substitution_id": sid, "strategy": s["strategy"]}
        zone_bn, cname, ebn, term = zname(z), c["name_bn"], e.get("name_bn", e["id"]), c["exam_term_bn"]
        text = s["text_bn"].strip(); grade = c.get("grade", 6)
        stu = [f"{cname} কী? আমাদের {zone_bn} এলাকার উদাহরণ দিয়ে সহজভাবে বোঝাও।",
               f"{cname} বিষয়টা {ebn} দিয়ে বুঝিয়ে দাও।",
               f"আমি {gen(zone_bn)} ছাত্র। {cname} সহজ করে বোঝাও, আমাদের চেনা উদাহরণ দিয়ে।",
               f"{gen(ebn)} সঙ্গে {gen(cname)} সম্পর্ক কী?",
               f"পরীক্ষায় '{term}' লিখতে হবে। জিনিসটা {ebn} দিয়ে বুঝিয়ে দাও যাতে মনে থাকে।"]
        for k in rng.sample(range(len(stu)), 2):
            out.append(rec("CONCEPT_EXPLANATION", "STUDENT", stu[k], text, prov, f"sub.student.v{k}"))
        tea = [f"শ্রেণি {bn(grade)}-এর জন্য {cname} পড়াতে {zone_bn} এলাকার একটি স্থানীয় উদাহরণ দিন।",
               f"{cname} বোঝাতে {ebn} দিয়ে একটি ব্যাখ্যা তৈরি করে দিন, ছাত্রছাত্রীরা যেন চেনা জিনিস দিয়ে বোঝে।",
               f"আমার ক্লাসে {cname} পড়াব। বইয়ের উদাহরণের সঙ্গে আমাদের এলাকার কোন উদাহরণ যোগ করা যায়?"]
        ut, k = pick(rng, tea, rng.randrange(3))
        at = (f"আপনি {ebn} দিয়ে শুরু করতে পারেন। ছাত্রছাত্রীদের এভাবে বলা যায়:\n\n{text}\n\n"
              f"পরীক্ষার পরিভাষা অবশ্যই থাকবে: {term}। বইয়ের মূল উদাহরণটিও একবার বলে দেবেন, স্থানীয় উদাহরণ তার সঙ্গে যোগ হবে, বদলে নয়।")
        if s.get("disanalogy_flags"):
            at += "\n\nসতর্কতা:\n" + "\n".join("- " + f for f in s["disanalogy_flags"])
        out.append(rec("TEACHER_PEDAGOGY", "TEACHER", ut, at, prov, f"sub.teacher.v{k}"))
        for flag in s.get("disanalogy_flags") or []:
            um = f"{ebn} দিয়ে {cname} বোঝানো হয়, তাহলে দুটো কি একই জিনিস?"
            am = (f"ভুল ধারণা: {ebn} আর {cname} একই রকম।\nকেন ভুল: {flag}\n"
                  f"সঠিক ধারণা: {ebn} শুধু ধারণাটা চেনাতে সাহায্য করে; পরীক্ষায় ও ব্যাখ্যায় {term} শব্দটাই ব্যবহার করবে।")
            out.append(rec("MISCONCEPTION_CORRECTION", "STUDENT", um, am, prov, "sub.misconception.flag"))
    return out


# ------------------------------------------------------------------ misconceptions -> corrections, teacher notes, T/F quiz
def from_misconceptions(store, rng, mis):
    out = []
    for i, m in enumerate(mis):
        c = store["concepts"].get(m["concept_id"])
        if not c:
            continue
        prov = {"concept_id": c["id"]}
        stu = [f"{m['wrong_bn']} ঠিক তো?", f"আমার বন্ধু বলে, {m['wrong_bn']} এটা কি সত্যি?", f"{c['name_bn']} নিয়ে একটা কথা শুনেছি: {m['wrong_bn']}"]
        u, k = pick(rng, stu, i)
        a = f"ভুল ধারণা: {m['wrong_bn']}\nকেন ভুল: {m['why_bn']}\nসঠিক ধারণা: {m['right_bn']}"
        out.append(rec("MISCONCEPTION_CORRECTION", "STUDENT", u, a, prov, f"mis.student.v{k}"))
        ut = [f"{c['name_bn']} পড়ানোর সময় ছাত্রছাত্রীরা কোন ভুল ধারণা নিয়ে আসে, আর কীভাবে শোধরাব?",
              f"শ্রেণি {bn(c.get('grade', 7))}-এ {c['name_bn']} পড়াতে গিয়ে একটি সাধারণ ভুল ধারণা ও তার সমাধান দিন।"]
        u2, k2 = pick(rng, ut, i)
        a2 = (f"একটি খুব সাধারণ ভুল ধারণা: \"{m['wrong_bn']}\"\n\nকেন হয়: {m['why_bn']}\n\n"
              f"ক্লাসে আপনি এভাবে শোধরাতে পারেন: প্রথমে ছাত্রছাত্রীদের ভুলটা নিজের মুখে বলতে দিন, তারপর একটি চেনা উদাহরণ দিয়ে দেখান যে "
              f"{m['right_bn']} শেষে বোর্ডে পরিভাষাটি লিখুন: {c['exam_term_bn']}।")
        out.append(rec("TEACHER_PEDAGOGY", "TEACHER", u2, a2, prov, f"mis.teacher.v{k2}"))
    return out


# ------------------------------------------------------------------ local-context Q/A from the store (entities + zones)
def from_local_context(store, rng):
    out = []
    zones = {zid: z for zid, z in store["zones"].items() if z.get("name_bn")}
    for e in store["entities"].values():
        ebn = e.get("name_bn"); note = (e.get("authenticity") or {}).get("note_bn")
        zs = [zname(zones[z]) for z in e.get("zones", []) if z in zones]
        if not (ebn and note and zs):
            continue
        prov = {"entity_id": e["id"]}
        where = ", ".join(zs)
        us = [f"{ebn} কী? আমাদের এলাকায় এটা কোথায় দেখা যায়?", f"{ebn} সম্পর্কে দু-লাইনে বলো।", f"পশ্চিমবঙ্গের কোন অঞ্চলে {ebn} বেশি চেনা?"]
        for k, u in enumerate(us):
            a = [f"{ebn}: {note}। পশ্চিমবঙ্গের {where} অঞ্চলে এটি খুব চেনা।",
                 f"{ebn} সম্পর্কে: {note}। মূলত {where} অঞ্চলে দেখা যায়।",
                 f"{ebn} সবচেয়ে বেশি চেনা {where} অঞ্চলে। {note}।"][k]
            out.append(rec("LOCAL_CONTEXT_QA", "STUDENT", u, a, prov, f"local.entity.v{k}"))
    for zid, z in zones.items():
        prov = {"zone_id": zid}; nb = zname(z)
        qa = [(f"{nb} অঞ্চলের প্রধান উৎসবগুলি কী কী?", "এই অঞ্চলে উদযাপিত প্রধান উৎসব: " + ", ".join(z.get("festivals_bn", [])) + "।"),
              (f"{nb} অঞ্চলে জমি বা জিনিস মাপার স্থানীয় একক কী?", "স্থানীয় একক: " + ", ".join(z.get("local_units_bn", [])) + "।"),
              (f"{nb} অঞ্চলটা কেমন? ছোট করে বলো।", z.get("context_bn", "") + "।"),
              (f"{nb} অঞ্চলে কোন কোন জেলা পড়ে?", "জেলাগুলি: " + ", ".join(district_bn(d) for d in z.get("districts", [])) + "।"),
              (f"{gen(nb)} ছাত্রছাত্রীদের রোজকার চেনা জায়গা কোনগুলো?", "রোজকার চেনা জায়গা: " + ", ".join(z.get("everyday_places_bn", [])) + "।"),
              (f"{nb} অঞ্চলে কোন ভাষাগুলি বলা হয়?", "প্রধান ভাষা: " + ", ".join(z.get("languages", [])) + "।")]
        for k, (u, a) in enumerate(qa):
            out.append(rec("LOCAL_CONTEXT_QA", "STUDENT", u, a, prov, f"local.zone.v{k}"))
    return out


# ------------------------------------------------------------------ programmatic worked sums (local context)
ITEMS = [("আম", "কেজি"), ("চাল", "কেজি"), ("ইলিশ মাছ", "কেজি"), ("আলু", "কেজি"), ("চা পাতা", "কেজি"), ("সরষের তেল", "লিটার"), ("কাজু", "কেজি"), ("গাঁদা ফুলের মালা", "টি"), ("কমলালেবু", "টি"), ("চিংড়ি", "কেজি")]
PLACES = [("হাটে", "gangetic_plain"), ("বাজারে", "kolkata_metro"), ("মাছের আড়তে", "sundarbans_delta"), ("চা-বাগানের দোকানে", "north_bengal_tea_belt"), ("পৌষমেলায়", "rarh_plateau"), ("দিঘার বাজারে", "medinipur_coastal")]
# plausible retail prices (Rs) per item so a sum never says rice is 8 Rs/kg
PRICES = {"আম": [40, 50, 60, 80, 100, 120], "চাল": [30, 35, 40, 45, 50, 60], "ইলিশ মাছ": [600, 800, 900, 1000, 1200, 1500], "আলু": [15, 20, 25, 30, 40],
          "চা পাতা": [200, 250, 300, 400], "সরষের তেল": [150, 160, 180, 200], "কাজু": [600, 700, 800, 900], "গাঁদা ফুলের মালা": [5, 8, 10, 15, 20],
          "কমলালেবু": [5, 8, 10, 12, 15], "চিংড়ি": [300, 400, 500, 600]}


def price_phrase(item, unit, p):
    """'আম ৮০ টাকা কেজি' / 'কমলালেবু একটি ১০ টাকা' (spoken market Bengali)."""
    return f"{item} একটি {bn(p)} টাকা" if unit == "টি" else f"{item} {bn(p)} টাকা {unit}"


def qty_phrase(item, unit, q):
    return f"{bn(q)}টি {item}" if unit == "টি" else f"{bn(q)} {unit} {item}"


def gen_percentage(store, rng, n):
    out = []
    for i in range(n):
        item, unit = rng.choice(ITEMS); place, zone = rng.choice(PLACES)
        price = rng.choice(PRICES[item]); pct = rng.choice([5, 10, 12, 15, 20, 25, 30, 40, 50])
        if (price * pct) % 100:
            continue
        disc = price * pct // 100; pay = price - disc
        us = [f"{place} {bn(price)} টাকা দামের {item} কিনতে {bn(pct)}% ছাড় পেলে কত টাকা দিতে হবে? ধাপে ধাপে দেখাও।",
              f"{price_phrase(item, unit, price)}। দোকানি {bn(pct)}% ছাড় দিল। ছাড়ের টাকা ও দাম কত?",
              f"{bn(price)} টাকার জিনিসে {bn(pct)}% ছাড়। কত ছাড় পাব?",
              f"{place} {gen(item)} দাম {bn(price)} টাকা থেকে {bn(pct)}% কমল। নতুন দাম কত? ধাপে ধাপে।"]
        u, k = pick(rng, us, i)
        a = worked([f"দেওয়া আছে: দাম {bn(price)} টাকা, ছাড় {bn(pct)}%।",
                    f"ধরি, ছাড়ের টাকা = {bn(price)} × {bn(pct)} ÷ ১০০।",
                    f"সূত্রানুসারে: {bn(price)} × {bn(pct)} ÷ ১০০ = {bn(price * pct)} ÷ ১০০ = {bn(disc)} টাকা।",
                    f"সমাধান: দিতে হবে {bn(price)} - {bn(disc)} = {bn(pay)} টাকা।"], f"ছাড় {bn(disc)} টাকা, দিতে হবে {bn(pay)} টাকা।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_percentage", "zone_id": zone}, f"sum.percentage.v{k}"))
    return out


def gen_percentage_of(store, rng, n):
    """percentage of a quantity / what percent: marks, attendance, yield, wage rise."""
    out = []
    for i in range(n):
        kind = i % 3
        if kind == 0:   # marks: x out of y -> %
            total = rng.choice([25, 50, 80, 100]); got = rng.choice([v for v in range(5, total + 1) if (v * 100) % total == 0])
            pct = got * 100 // total; subj = rng.choice(["গণিত", "পরিবেশ ও বিজ্ঞান", "বাংলা", "ইংরেজি"])
            u = f"{subj} পরীক্ষায় {bn(total)}-এর মধ্যে {bn(got)} পেলে কত শতাংশ নম্বর? ধাপে ধাপে দেখাও।"
            a = worked([f"দেওয়া আছে: মোট নম্বর {bn(total)}, প্রাপ্ত নম্বর {bn(got)}।", "সূত্রানুসারে: শতাংশ = প্রাপ্ত ÷ মোট × ১০০।",
                        f"সমাধান: {bn(got)} ÷ {bn(total)} × ১০০ = {bn(pct)}%।"], f"{bn(pct)}% নম্বর।")
            zone = "gangetic_plain"
        elif kind == 1:  # attendance
            total = rng.choice([20, 25, 40, 50]); present = rng.choice([v for v in range(5, total + 1) if (v * 100) % total == 0])
            pct = present * 100 // total
            u = f"ক্লাসে {bn(total)} জনের মধ্যে {bn(present)} জন উপস্থিত। উপস্থিতির শতকরা হার কত? ধাপে ধাপে।"
            a = worked([f"দেওয়া আছে: মোট ছাত্রছাত্রী {bn(total)}, উপস্থিত {bn(present)}।", "সূত্রানুসারে: শতকরা = উপস্থিত ÷ মোট × ১০০।",
                        f"সমাধান: {bn(present)} ÷ {bn(total)} × ১০০ = {bn(pct)}%।"], f"উপস্থিতি {bn(pct)}%।")
            zone = "rarh_plateau"
        else:            # wage / price rise
            base = rng.choice([200, 250, 300, 500, 600]); pct = rng.choice([5, 10, 20, 25]); rise = base * pct // 100
            if (base * pct) % 100:
                continue
            ctx = rng.choice([("চা-শ্রমিকের দৈনিক মজুরি", "north_bengal_tea_belt"), ("কাজুর কেজি-দর", "medinipur_coastal"), ("টোটোর ভাড়া", "gangetic_plain")])
            u = f"{ctx[0]} {bn(base)} টাকা থেকে {bn(pct)}% বাড়লে নতুন পরিমাণ কত? ধাপে ধাপে দেখাও।"
            a = worked([f"দেওয়া আছে: আগের পরিমাণ {bn(base)} টাকা, বৃদ্ধি {bn(pct)}%।", f"সূত্রানুসারে: বৃদ্ধি = {bn(base)} × {bn(pct)} ÷ ১০০ = {bn(rise)} টাকা।",
                        f"সমাধান: নতুন পরিমাণ = {bn(base)} + {bn(rise)} = {bn(base + rise)} টাকা।"], f"{bn(base + rise)} টাকা।")
            zone = ctx[1]
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_percentage", "zone_id": zone}, f"sum.pctof.v{kind}"))
    return out


def gen_simple_interest(store, rng, n):
    out = []
    for i in range(n):
        p = rng.choice([500, 1000, 1500, 2000, 2500, 4000, 5000, 8000, 10000]); r = rng.choice([4, 5, 6, 8, 10, 12]); t = rng.choice([1, 2, 3, 4, 5])
        if (p * r * t) % 100:
            continue
        si = p * r * t // 100
        ctx = rng.choice(["হালখাতায় দোকানের ধার", "সমবায় ব্যাংকে জমা", "স্বনির্ভর গোষ্ঠীর ঋণ", "ডাকঘরে জমা", "ভেড়ির চাষে ঋণ", "সবুজসাথী সাইকেল মেরামতের জন্য ধার"])
        us = [f"{ctx}: {bn(p)} টাকা, বার্ষিক {bn(r)}% সরল সুদে {bn(t)} বছরে সুদ কত হবে? ধাপে ধাপে বোঝাও।",
              f"{bn(p)} টাকার {bn(t)} বছরের সরল সুদ কত, যদি হার বছরে {bn(r)}% হয়? সুদ-আসলও বলো।",
              f"{ctx} নেওয়া {bn(p)} টাকা {bn(r)}% বার্ষিক সরল সুদে {bn(t)} বছর পর মোট কত ফেরত দিতে হবে?"]
        u, k = pick(rng, us, i)
        a = worked([f"দেওয়া আছে: আসল = {bn(p)} টাকা, সুদের হার = {bn(r)}%, সময় = {bn(t)} বছর।",
                    "সূত্রানুসারে: সরল সুদ = আসল × হার × সময় ÷ ১০০।",
                    f"সমাধান: {bn(p)} × {bn(r)} × {bn(t)} ÷ ১০০ = {bn(p * r * t)} ÷ ১০০ = {bn(si)} টাকা।",
                    f"সুদ-আসল = {bn(p)} + {bn(si)} = {bn(p + si)} টাকা।"], f"সুদ {bn(si)} টাকা, সুদ-আসল {bn(p + si)} টাকা।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_si", "zone_id": "gangetic_plain"}, f"sum.si.v{k}"))
    return out


def gen_ratio(store, rng, n):
    out = []
    for i in range(n):
        a_, b_ = rng.choice([(3, 1), (2, 1), (4, 1), (3, 2), (5, 2), (5, 3)]); k = rng.choice([2, 3, 4, 5, 6, 8, 10, 12])
        rice = a_ * k; dal = b_ * k
        ctx = rng.choice([("মিড-ডে মিলের খিচুড়িতে চাল ও ডাল", "কেজি", "rarh_plateau"), ("মালায় গাঁদা ও রজনীগন্ধা", "টি", "medinipur_coastal"),
                          ("চায়ের দোকানে দুধ ও জল", "কাপ", "north_bengal_tea_belt"), ("ভেড়িতে বাগদা ও গলদা", "কেজি", "sundarbans_delta")])
        us = [f"{gen(ctx[0])} অনুপাত {bn(a_)} : {bn(b_)}। প্রথমটি {bn(rice)} {ctx[1]} হলে দ্বিতীয়টি কত? ধাপে ধাপে দেখাও।",
              f"{ctx[0]} {bn(a_)} : {bn(b_)} অনুপাতে রাখতে হবে। {bn(rice)} {ctx[1]} প্রথমটির সঙ্গে দ্বিতীয়টি কত লাগবে?"]
        u, kk = pick(rng, us, i)
        a = worked([f"দেওয়া আছে: অনুপাত = {bn(a_)} : {bn(b_)}, প্রথম পরিমাণ = {bn(rice)} {ctx[1]}।",
                    f"ধরি, দ্বিতীয় পরিমাণ = x। তাহলে {bn(a_)} : {bn(b_)} = {bn(rice)} : x।",
                    f"সূত্রানুসারে: {bn(a_)} × x = {bn(b_)} × {bn(rice)}, অর্থাৎ x = {bn(b_ * rice)} ÷ {bn(a_)} = {bn(dal)}।"], f"{bn(dal)} {ctx[1]}।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_ratio", "zone_id": ctx[2]}, f"sum.ratio.v{kk}"))
    return out


def gen_units(store, rng, n):
    out = []
    for i in range(n):
        kind = i % 5
        if kind == 0:
            b = rng.randint(1, 8); k = rng.choice([0, 3, 5, 8, 10, 12, 15, 18]); total = b * 20 + k; crop = rng.choice(["ধান", "আলু", "সরষে", "পাট", "পান"])
            u = f"{bn(b)} বিঘা {bn(k)} কাঠা জমিতে {crop} চাষ হবে। মোট কত কাঠা? (১ বিঘা = ২০ কাঠা) ধাপে ধাপে দেখাও।"
            a = worked([f"দেওয়া আছে: {bn(b)} বিঘা {bn(k)} কাঠা; ১ বিঘা = ২০ কাঠা।", f"সূত্রানুসারে: {bn(b)} বিঘা = {bn(b)} × ২০ = {bn(b * 20)} কাঠা।",
                        f"সমাধান: মোট = {bn(b * 20)} + {bn(k)} = {bn(total)} কাঠা।"], f"{bn(total)} কাঠা।"); zone = "rarh_plateau"
        elif kind == 1:
            kg = rng.randint(1, 9); g = rng.choice([0, 250, 500, 750]); total = kg * 1000 + g; item = rng.choice(["চিংড়ি", "ইলিশ", "আলু", "চা পাতা", "কাজু"])
            u = f"আড়তে {item} {bn(kg)} কেজি {bn(g)} গ্রাম। মোট কত গ্রাম? ধাপে ধাপে দেখাও।"
            a = worked([f"দেওয়া আছে: {bn(kg)} কেজি {bn(g)} গ্রাম; ১ কেজি = ১০০০ গ্রাম।", f"সূত্রানুসারে: {bn(kg)} কেজি = {bn(kg)} × ১০০০ = {bn(kg * 1000)} গ্রাম।",
                        f"সমাধান: মোট = {bn(kg * 1000)} + {bn(g)} = {bn(total)} গ্রাম।"], f"{bn(total)} গ্রাম।"); zone = "sundarbans_delta"
        elif kind == 2:
            km = rng.randint(1, 9); m = rng.choice([0, 200, 500, 750]); total = km * 1000 + m; ride = rng.choice(["টোটোয়", "সাইকেলে", "হেঁটে"])
            u = f"বাড়ি থেকে স্কুল {ride} {bn(km)} কিমি {bn(m)} মিটার। মোট কত মিটার? ধাপে ধাপে।"
            a = worked([f"দেওয়া আছে: {bn(km)} কিমি {bn(m)} মিটার; ১ কিমি = ১০০০ মিটার।", f"সূত্রানুসারে: {bn(km)} কিমি = {bn(km)} × ১০০০ = {bn(km * 1000)} মিটার।",
                        f"সমাধান: মোট = {bn(km * 1000)} + {bn(m)} = {bn(total)} মিটার।"], f"{bn(total)} মিটার।"); zone = "north_bengal_tea_belt"
        elif kind == 3:
            lt = rng.randint(1, 9); ml = rng.choice([0, 250, 500, 750]); total = lt * 1000 + ml
            liquid = rng.choice([("মিড-ডে মিলে", "সরষের তেল"), ("চায়ের দোকানে", "দুধ"), ("পুজোর ভোগে", "ঘি"), ("খেজুর রসের হাঁড়িতে", "রস")])
            u = f"{liquid[0]} {bn(lt)} লিটার {bn(ml)} মিলিলিটার {liquid[1]} লাগে। মোট কত মিলিলিটার? ধাপে ধাপে।"
            a = worked([f"দেওয়া আছে: {bn(lt)} লিটার {bn(ml)} মিলি; ১ লিটার = ১০০০ মিলি।", f"সূত্রানুসারে: {bn(lt)} লিটার = {bn(lt)} × ১০০০ = {bn(lt * 1000)} মিলি।",
                        f"সমাধান: মোট = {bn(lt * 1000)} + {bn(ml)} = {bn(total)} মিলি।"], f"{bn(total)} মিলিলিটার।"); zone = "gangetic_plain"
        else:
            h = rng.randint(1, 9); mi = rng.choice([0, 10, 15, 20, 30, 40, 45, 50]); total = h * 60 + mi
            ctx = rng.choice(["টয় ট্রেনের যাত্রা", "লঞ্চে গঙ্গাসাগর", "মেট্রোয় অপেক্ষা ও যাত্রা", "হাটে কেনাকাটা", "চা-বাগানে পাতা তোলা", "পুজোর অঞ্জলি ও প্রসাদ"])
            u = f"{ctx} {bn(h)} ঘণ্টা {bn(mi)} মিনিট লাগে। মোট কত মিনিট? ধাপে ধাপে।"
            a = worked([f"দেওয়া আছে: {bn(h)} ঘণ্টা {bn(mi)} মিনিট; ১ ঘণ্টা = ৬০ মিনিট।", f"সূত্রানুসারে: {bn(h)} ঘণ্টা = {bn(h)} × ৬০ = {bn(h * 60)} মিনিট।",
                        f"সমাধান: মোট = {bn(h * 60)} + {bn(mi)} = {bn(total)} মিনিট।"], f"{bn(total)} মিনিট।"); zone = "kolkata_metro"
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_unitconv", "zone_id": zone}, f"sum.unit.v{kind}"))
    return out


def gen_speed(store, rng, n):
    vehicles = [("টোটো", (18, 20, 25), "north_bengal_tea_belt"), ("সাইকেল", (10, 12, 15), "gangetic_plain"), ("মেট্রো", (40, 45, 50), "kolkata_metro"), ("লঞ্চ", (12, 15, 18), "sundarbans_delta"),
                ("ট্রাম", (15, 18, 20), "kolkata_metro"), ("টয় ট্রেন", (8, 10, 12), "north_bengal_tea_belt"), ("হলুদ ট্যাক্সি", (24, 30, 36), "kolkata_metro"), ("নৌকা", (5, 6, 8), "sundarbans_delta"),
                ("বাস", (30, 35, 40), "medinipur_coastal"), ("গরুর গাড়ি", (4, 5, 6), "rarh_plateau"), ("ভ্যান রিকশা", (10, 12, 14), "medinipur_coastal"), ("লোকাল ট্রেন", (50, 60, 70), "gangetic_plain")]
    out = []
    for i in range(n):
        v, speeds, zone = rng.choice(vehicles); speed = rng.choice(speeds); t = rng.choice([1, 2, 3, 4, 5, 6, 7, 8]); d = speed * t; kind = i % 3
        if kind == 0:
            u = f"একটি {v} {bn(speed)} কিমি/ঘণ্টা বেগে {bn(t)} ঘণ্টা চললে কত দূর যাবে? ধাপে ধাপে দেখাও।"
            a = worked([f"দেওয়া আছে: গতিবেগ = {bn(speed)} কিমি/ঘণ্টা, সময় = {bn(t)} ঘণ্টা।", "সূত্রানুসারে: দূরত্ব = গতিবেগ × সময়।",
                        f"সমাধান: {bn(speed)} × {bn(t)} = {bn(d)} কিমি।"], f"{bn(d)} কিমি।")
        elif kind == 1:
            u = f"{gen(v)} গতিবেগ {bn(speed)} কিমি/ঘণ্টা। {bn(d)} কিমি যেতে কত সময় লাগবে? ধাপে ধাপে।"
            a = worked([f"দেওয়া আছে: গতিবেগ = {bn(speed)} কিমি/ঘণ্টা, দূরত্ব = {bn(d)} কিমি।", "সূত্রানুসারে: সময় = দূরত্ব ÷ গতিবেগ।",
                        f"সমাধান: {bn(d)} ÷ {bn(speed)} = {bn(t)} ঘণ্টা।"], f"{bn(t)} ঘণ্টা।")
        else:
            u = f"একটি {v} {bn(t)} ঘণ্টায় {bn(d)} কিমি গেল। গতিবেগ কত? ধাপে ধাপে দেখাও।"
            a = worked([f"দেওয়া আছে: দূরত্ব = {bn(d)} কিমি, সময় = {bn(t)} ঘণ্টা।", "সূত্রানুসারে: গতিবেগ = দূরত্ব ÷ সময়।",
                        f"সমাধান: {bn(d)} ÷ {bn(t)} = {bn(speed)} কিমি/ঘণ্টা।"], f"{bn(speed)} কিমি/ঘণ্টা।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_speed", "zone_id": zone}, f"sum.speed.v{kind}"))
    return out


def gen_area(store, rng, n):
    things = [("পুকুর", "gangetic_plain"), ("ধানখেত", "gangetic_plain"), ("স্কুলের মাঠ", "rarh_plateau"), ("চা-বাগানের একটি অংশ", "north_bengal_tea_belt"),
              ("পান বরজ", "medinipur_coastal"), ("চিংড়ি ভেড়ি", "sundarbans_delta"), ("পুজোর প্যান্ডেলের মেঝে", "kolkata_metro")]
    out = []
    for i in range(n):
        L = rng.choice([20, 24, 25, 30, 36, 40, 50, 60]); W = rng.choice([8, 10, 12, 15, 18, 20, 25, 30]); W = W if W < L else L // 2
        thing, zone = rng.choice(things); kind = i % 3
        if kind == 0:
            u = f"একটি আয়তাকার {thing} {bn(L)} মিটার লম্বা ও {bn(W)} মিটার চওড়া। এর পরিসীমা ও ক্ষেত্রফল কত? ধাপে ধাপে দেখাও।"
            a = worked([f"দেওয়া আছে: দৈর্ঘ্য = {bn(L)} মি, প্রস্থ = {bn(W)} মি।",
                        f"সূত্রানুসারে: পরিসীমা = ২ × (দৈর্ঘ্য + প্রস্থ) = ২ × ({bn(L)} + {bn(W)}) = ২ × {bn(L + W)} = {bn(2 * (L + W))} মি।",
                        f"ক্ষেত্রফল = দৈর্ঘ্য × প্রস্থ = {bn(L)} × {bn(W)} = {bn(L * W)} বর্গমিটার।"], f"পরিসীমা {bn(2 * (L + W))} মিটার, ক্ষেত্রফল {bn(L * W)} বর্গমিটার।")
        elif kind == 1:
            u = f"{gen(thing)} চারদিকে বেড়া দিতে হবে। জমি {bn(L)} মি × {bn(W)} মি হলে কত মিটার বেড়া লাগবে? ধাপে ধাপে।"
            a = worked([f"দেওয়া আছে: দৈর্ঘ্য = {bn(L)} মি, প্রস্থ = {bn(W)} মি; বেড়া = পরিসীমা।", "সূত্রানুসারে: পরিসীমা = ২ × (দৈর্ঘ্য + প্রস্থ)।",
                        f"সমাধান: ২ × ({bn(L)} + {bn(W)}) = {bn(2 * (L + W))} মিটার।"], f"{bn(2 * (L + W))} মিটার বেড়া।")
        else:
            s = rng.choice([4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 18, 20, 25, 30])
            u = f"একটি বর্গাকার {gen(thing)} এক বাহু {bn(s)} মিটার। পরিসীমা ও ক্ষেত্রফল কত? ধাপে ধাপে দেখাও।"
            a = worked([f"দেওয়া আছে: বাহু = {bn(s)} মি।", f"সূত্রানুসারে: বর্গের পরিসীমা = ৪ × বাহু = ৪ × {bn(s)} = {bn(4 * s)} মি।",
                        f"ক্ষেত্রফল = বাহু × বাহু = {bn(s)} × {bn(s)} = {bn(s * s)} বর্গমিটার।"], f"পরিসীমা {bn(4 * s)} মিটার, ক্ষেত্রফল {bn(s * s)} বর্গমিটার।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_area", "zone_id": zone}, f"sum.area.v{kind}"))
    return out


def gen_mean(store, rng, n):
    ctxs = [("এক চা-শ্রমিকের দৈনিক পাতা তোলা (কেজি)", "north_bengal_tea_belt"), ("এক সপ্তাহের হাটে বিক্রি (কেজি)", "gangetic_plain"), ("পাঁচ দিনের বৃষ্টি (মিমি)", "sundarbans_delta"),
            ("ইলিশের কেজি-দর (টাকা)", "kolkata_metro"), ("ক্লাসের পাঁচ ছাত্রের নম্বর", "rarh_plateau"), ("গাঁদা ফুলের দৈনিক বিক্রি (মালা)", "medinipur_coastal")]
    out = []
    for i in range(n):
        k = rng.choice([4, 5, 6]); vals = [rng.randint(12, 40) for _ in range(k)]
        while sum(vals) % k:
            vals[-1] += 1
        mean = sum(vals) // k; ctx, zone = rng.choice(ctxs); vs = ", ".join(bn(v) for v in vals); kind = i % 2
        if kind == 0:
            u = f"{ctx}: {vs}। গড় কত? ধাপে ধাপে দেখাও।"
            a = worked([f"দেওয়া আছে: রাশিগুলি {vs}; রাশির সংখ্যা {bn(k)}।", "সূত্রানুসারে: গড় = রাশিগুলির যোগফল ÷ রাশির সংখ্যা।",
                        f"সমাধান: যোগফল = {bn(sum(vals))}; গড় = {bn(sum(vals))} ÷ {bn(k)} = {bn(mean)}।"], f"গড় {bn(mean)}।")
        else:
            sv = sorted(vals); med = sv[k // 2] if k % 2 else (sv[k // 2 - 1] + sv[k // 2]) / 2
            u = f"{ctx}: {vs}। মধ্যমা কত? ধাপে ধাপে দেখাও।"
            a = worked([f"দেওয়া আছে: রাশিগুলি {vs}; রাশির সংখ্যা {bn(k)}।", f"ধরি, রাশিগুলি ছোট থেকে বড় সাজাই: {', '.join(bn(v) for v in sv)}।",
                        ("সূত্রানুসারে: রাশির সংখ্যা বিজোড়, তাই মাঝের রাশিই মধ্যমা।" if k % 2 else "সূত্রানুসারে: রাশির সংখ্যা জোড়, তাই মাঝের দুটি রাশির গড়ই মধ্যমা।"),
                        f"সমাধান: মধ্যমা = {bn(med)}।"], f"মধ্যমা {bn(med)}।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_mean", "zone_id": zone}, f"sum.mean.v{kind}"))
    return out


def gen_profit_loss(store, rng, n):
    out = []
    for i in range(n):
        item, zone = rng.choice([("ইলিশ", "sundarbans_delta"), ("আলু", "gangetic_plain"), ("আম", "north_bengal_tea_belt"), ("কাজু", "medinipur_coastal"), ("গাঁদার মালা", "medinipur_coastal"), ("কাঁকড়া", "sundarbans_delta"), ("লাক্ষা", "rarh_plateau")])
        cp = rng.choice([5, 8, 10, 40, 60, 80, 100, 150, 200, 400, 600]); delta = rng.choice([-30, -20, -10, -5, 3, 5, 10, 20, 40, 50]); sp = cp + delta
        if sp <= 0:
            continue
        kind = i % 2; kd = "লাভ" if delta > 0 else "ক্ষতি"
        if kind == 0:
            u = f"এক বিক্রেতা {item} প্রতি কেজি {bn(cp)} টাকায় কিনে {bn(sp)} টাকায় বেচলেন। লাভ না ক্ষতি, কত? ধাপে ধাপে দেখাও।"
            a = worked([f"দেওয়া আছে: ক্রয়মূল্য = {bn(cp)} টাকা, বিক্রয়মূল্য = {bn(sp)} টাকা।",
                        ("সূত্রানুসারে: বিক্রয়মূল্য > ক্রয়মূল্য, তাই লাভ = বিক্রয়মূল্য - ক্রয়মূল্য।" if delta > 0 else "সূত্রানুসারে: ক্রয়মূল্য > বিক্রয়মূল্য, তাই ক্ষতি = ক্রয়মূল্য - বিক্রয়মূল্য।"),
                        f"সমাধান: {bn(max(cp, sp))} - {bn(min(cp, sp))} = {bn(abs(delta))} টাকা।"], f"প্রতি কেজিতে {kd} {bn(abs(delta))} টাকা।")
        else:
            if (abs(delta) * 100) % cp:
                continue
            pct = abs(delta) * 100 // cp
            u = f"{item} {bn(cp)} টাকায় কিনে {bn(sp)} টাকায় বেচলে শতকরা {kd} কত? ধাপে ধাপে।"
            a = worked([f"দেওয়া আছে: ক্রয়মূল্য = {bn(cp)} টাকা, বিক্রয়মূল্য = {bn(sp)} টাকা।", f"ধরি, {kd} = {bn(abs(delta))} টাকা।",
                        f"সূত্রানুসারে: শতকরা {kd} = {kd} ÷ ক্রয়মূল্য × ১০০ = {bn(abs(delta))} ÷ {bn(cp)} × ১০০ = {bn(pct)}%।"], f"শতকরা {kd} {bn(pct)}%।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_profitloss", "zone_id": zone}, f"sum.pl.v{kind}"))
    return out


def gen_fraction(store, rng, n):
    things = [("কাজু", "medinipur_coastal"), ("মুড়ির মোয়া", "gangetic_plain"), ("কমলালেবু", "north_bengal_tea_belt"), ("পিঠে", "gangetic_plain"), ("আম", "north_bengal_tea_belt"), ("গাঁদা ফুল", "medinipur_coastal")]
    out = []
    for i in range(n):
        den = rng.choice([2, 3, 4, 5, 6]); num = rng.randint(1, den - 1); total = den * rng.choice([2, 3, 4, 5, 6]); part = total * num // den; thing, zone = rng.choice(things)
        kind = i % 2
        if kind == 0:
            u = f"{bn(total)}টি {thing}-এর {bn(num)}/{bn(den)} অংশ কতগুলি? ধাপে ধাপে দেখাও।"
            a = worked([f"দেওয়া আছে: মোট {bn(total)}টি, অংশ {bn(num)}/{bn(den)}।", f"সূত্রানুসারে: {bn(num)}/{bn(den)} অংশ = মোট ÷ {bn(den)} × {bn(num)}।",
                        f"সমাধান: {bn(total)} ÷ {bn(den)} = {bn(total // den)}; {bn(total // den)} × {bn(num)} = {bn(part)}টি।"], f"{bn(part)}টি {thing}।")
        else:
            u = f"{bn(total)}টি {thing} {bn(den)} জনে সমান ভাগ করলে প্রত্যেকে কতগুলি পাবে, আর সেটা মোটের কত অংশ? ধাপে ধাপে।"
            a = worked([f"দেওয়া আছে: মোট {bn(total)}টি, ভাগ {bn(den)} জনে।", f"সমাধান: প্রত্যেকে পায় {bn(total)} ÷ {bn(den)} = {bn(total // den)}টি।",
                        f"সেটা মোটের ১/{bn(den)} অংশ।"], f"প্রত্যেকে {bn(total // den)}টি, অর্থাৎ ১/{bn(den)} অংশ।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_fraction", "zone_id": zone}, f"sum.fraction.v{kind}"))
    return out


def gen_multiplication(store, rng, n):
    things = [("মুড়ির ঠোঙা", "gangetic_plain"), ("কমলালেবু", "north_bengal_tea_belt"), ("কাঁকড়া", "sundarbans_delta"), ("গাঁদার মালা", "medinipur_coastal"), ("কাজু", "medinipur_coastal"), ("পিঠে", "rarh_plateau")]
    out = []
    for i in range(n):
        a_ = rng.randint(2, 9); b_ = rng.randint(2, 9); thing, zone = rng.choice(things); kid = rng.choice(KIDS); kind = i % 2
        if kind == 0:
            u = f"{kid} {bn(a_)}টি ঝুড়িতে {bn(b_)}টি করে {thing} রাখল। মোট কতগুলি? ধাপে ধাপে দেখাও।"
            a = worked([f"দেওয়া আছে: {bn(a_)}টি ঝুড়ি, প্রতিটিতে {bn(b_)}টি।", f"সূত্রানুসারে: মোট = ঝুড়ির সংখ্যা × প্রতি ঝুড়িতে সংখ্যা = {bn(a_)} × {bn(b_)}।",
                        f"সমাধান: {bn(a_)} × {bn(b_)} = {bn(a_ * b_)}টি।"], f"{bn(a_ * b_)}টি {thing}।")
        else:
            tot = a_ * b_
            u = f"{bn(tot)}টি {thing} {bn(a_)} জনে সমান ভাগ করলে প্রত্যেকে কতগুলি পাবে? ধাপে ধাপে।"
            a = worked([f"দেওয়া আছে: মোট {bn(tot)}টি, ভাগ {bn(a_)} জনে।", "সূত্রানুসারে: প্রত্যেকের ভাগ = মোট ÷ জন।",
                        f"সমাধান: {bn(tot)} ÷ {bn(a_)} = {bn(b_)}টি।"], f"{bn(b_)}টি করে।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_addition", "zone_id": zone}, f"sum.mult.v{kind}"))
    return out


def gen_calendar(store, rng, n):
    out = []
    for i in range(n):
        kind = i % 3
        if kind == 0:
            m = rng.randrange(12); k = rng.randint(1, 5); target = (m + k) % 12
            u = f"{BANGLA_MONTHS[m]} মাসের {bn(k)} মাস পরে কোন মাস? ধাপে ধাপে দেখাও।"
            a = worked([f"দেওয়া আছে: শুরু {BANGLA_MONTHS[m]}, {bn(k)} মাস পরে।", "সূত্রানুসারে: বাংলা মাসের ক্রম: " + ", ".join(BANGLA_MONTHS) + "।",
                        f"সমাধান: {gen(BANGLA_MONTHS[m])} পরে {bn(k)} মাস গুনলে {BANGLA_MONTHS[target]}।"], f"{BANGLA_MONTHS[target]} মাস।")
        elif kind == 1:
            w = rng.randint(2, 9); d = rng.choice([0, 1, 2, 3, 4, 5, 6]); total = w * 7 + d; ctx = rng.choice(["পুজোর ছুটি", "ধান কাটা শেষ হতে", "মেলা চলবে"])
            u = f"{ctx} {bn(w)} সপ্তাহ {bn(d)} দিন। মোট কত দিন? ধাপে ধাপে।"
            a = worked([f"দেওয়া আছে: {bn(w)} সপ্তাহ {bn(d)} দিন; ১ সপ্তাহ = ৭ দিন।", f"সূত্রানুসারে: {bn(w)} সপ্তাহ = {bn(w)} × ৭ = {bn(w * 7)} দিন।",
                        f"সমাধান: মোট = {bn(w * 7)} + {bn(d)} = {bn(total)} দিন।"], f"{bn(total)} দিন।")
        else:
            h1 = rng.randint(6, 10); h2 = rng.randint(h1 + 1, 16); ctx = rng.choice(["স্কুল", "হাট", "পুজোর অঞ্জলি", "টয় ট্রেন"])
            u = f"{ctx} সকাল {bn(h1)}টায় শুরু হয়ে {bn(h2 if h2 <= 12 else h2 - 12)}টায় শেষ হলে কত ঘণ্টা চলল? ({'বিকেল' if h2 > 12 else 'সকাল'}) ধাপে ধাপে।"
            a = worked([f"দেওয়া আছে: শুরু {bn(h1)}টা, শেষ {bn(h2)}টা (২৪ ঘণ্টার হিসাবে)।", "সূত্রানুসারে: সময়কাল = শেষ - শুরু।",
                        f"সমাধান: {bn(h2)} - {bn(h1)} = {bn(h2 - h1)} ঘণ্টা।"], f"{bn(h2 - h1)} ঘণ্টা।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_calendar", "zone_id": "gangetic_plain"}, f"sum.calendar.v{kind}"))
    return out


def gen_money(store, rng, n):
    """Shopping totals and change at the haat: multiplication + addition + subtraction (grades 3-5)."""
    out = []
    for i in range(n):
        (i1, u1), (i2, u2) = rng.sample(ITEMS, 2); place, zone = rng.choice(PLACES)
        q1, q2 = rng.randint(1, 5), rng.randint(1, 5); p1 = rng.choice(PRICES[i1]); p2 = rng.choice(PRICES[i2])
        c1, c2 = q1 * p1, q2 * p2; total = c1 + c2; kid = rng.choice(KIDS); kind = i % 2
        note = next((x for x in (100, 200, 500, 1000, 2000, 5000, 10000) if x >= total), (total // 1000 + 1) * 1000)
        if kind == 0:
            u = f"{kid} {place} {qty_phrase(i1, u1, q1)} ({rate_phrase(u1, p1)}) আর {qty_phrase(i2, u2, q2)} ({rate_phrase(u2, p2)}) কিনল। মোট কত টাকা লাগল? ধাপে ধাপে দেখাও।"
            a = worked([f"দেওয়া আছে: {qty_phrase(i1, u1, q1)} × {bn(p1)} টাকা, {qty_phrase(i2, u2, q2)} × {bn(p2)} টাকা।",
                        f"সূত্রানুসারে: {gen(i1)} দাম = {bn(q1)} × {bn(p1)} = {bn(c1)} টাকা; {gen(i2)} দাম = {bn(q2)} × {bn(p2)} = {bn(c2)} টাকা।",
                        f"সমাধান: মোট = {bn(c1)} + {bn(c2)} = {bn(total)} টাকা।"], f"{bn(total)} টাকা।")
        else:
            u = f"{kid} {place} মোট {bn(total)} টাকার জিনিস কিনে {bn(note)} টাকার নোট দিল। কত টাকা ফেরত পাবে? ধাপে ধাপে।"
            a = worked([f"দেওয়া আছে: দাম {bn(total)} টাকা, দেওয়া হল {bn(note)} টাকা।", "সূত্রানুসারে: ফেরত = দেওয়া টাকা - দাম।",
                        f"সমাধান: {bn(note)} - {bn(total)} = {bn(note - total)} টাকা।"], f"{bn(note - total)} টাকা ফেরত।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_addition", "zone_id": zone}, f"sum.money.v{kind}"))
    return out


def gen_compare(store, rng, n):
    """Number sense with local prices and weights: compare, order, difference (grades 3-5)."""
    out = []
    for i in range(n):
        kind = i % 2
        if kind == 0:
            (i1, u1), (i2, u2) = rng.sample([x for x in ITEMS if x[1] == "কেজি"], 2); p1 = rng.choice(PRICES[i1]); p2 = rng.choice(PRICES[i2])
            if p1 == p2:
                continue
            big = (i1, p1) if p1 > p2 else (i2, p2); small = (i2, p2) if p1 > p2 else (i1, p1)
            u = f"হাটে {price_phrase(i1, u1, p1)} আর {price_phrase(i2, u2, p2)}। কোনটা দামি, আর কেজিতে কত বেশি? ধাপে ধাপে দেখাও।"
            a = worked([f"দেওয়া আছে: {i1} {bn(p1)} টাকা, {i2} {bn(p2)} টাকা।", f"সূত্রানুসারে: {bn(big[1])} > {bn(small[1])}, তাই {big[0]} দামি।",
                        f"সমাধান: পার্থক্য = {bn(big[1])} - {bn(small[1])} = {bn(big[1] - small[1])} টাকা।"], f"{big[0]} দামি, {bn(big[1] - small[1])} টাকা বেশি।")
            zone = "gangetic_plain"
        else:
            k = rng.choice([3, 4]); pairs = rng.sample(ITEMS, k); ws = rng.sample([250, 500, 750, 1000, 1250, 1500, 2000, 2500, 3000], k)
            listing = ", ".join(f"{it} {bn(w)} গ্রাম" for (it, _), w in zip(pairs, ws)); order = sorted(zip(ws, [p[0] for p in pairs]))
            u = f"ব্যাগে আছে {listing}। হালকা থেকে ভারী সাজাও। ধাপে ধাপে।"
            a = worked([f"দেওয়া আছে: {listing}।", "সূত্রানুসারে: গ্রামের সংখ্যা যত ছোট, জিনিস তত হালকা।",
                        "সমাধান: " + " < ".join(f"{it} ({bn(w)})" for w, it in order) + "।"], "হালকা থেকে ভারী: " + ", ".join(it for _, it in order) + "।")
            zone = "sundarbans_delta"
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_addition", "zone_id": zone}, f"sum.compare.v{kind}"))
    return out


# ------------------------------------------------------------------ FLN stories, quizzes, lesson plans, worksheets
def gen_fln_story(store, rng, n):
    things = [("আম", "north_bengal_tea_belt"), ("মুড়ির মোয়া", "gangetic_plain"), ("নারকেল", "sundarbans_delta"), ("কাঁঠালের কোয়া", "rarh_plateau"), ("লাল ফুল", "gangetic_plain"),
              ("ঘুড়ি", "kolkata_metro"), ("কমলালেবু", "north_bengal_tea_belt"), ("কাজু", "medinipur_coastal"), ("গাঁদা ফুল", "medinipur_coastal"), ("কাঁকড়া", "sundarbans_delta"), ("পিঠে", "rarh_plateau")]
    places = ["পার্কে", "পুকুরপাড়ে", "স্কুলের মাঠে", "হাটে", "বাগানে", "নদীর ঘাটে", "চা-বাগানে"]
    out = []
    for i in range(n):
        a_, b_ = rng.randint(1, 9), rng.randint(1, 9); k1, k2 = rng.sample(KIDS, 2); thing, zone = rng.choice(things); place = rng.choice(places)
        s = a_ + b_; sub = rng.randint(1, s); kind = i % 4
        us = [f"দ্বিতীয় শ্রেণির জন্য একটি ছোট গল্প লেখো যাতে যোগ ({bn(a_)} + {bn(b_)}) শেখানো যায়।",
              f"ছোটদের জন্য {thing} দিয়ে যোগ-বিয়োগের একটা গল্প বানাও।",
              f"প্রথম শ্রেণির বাচ্চাদের জন্য {k1}কে নিয়ে গোনার একটা গল্প বলো।",
              f"{thing} দিয়ে {bn(a_)} + {bn(b_)} বোঝানোর একটা ছোট গল্প লেখো, শেষে একটা প্রশ্ন রেখো।"]
        u = us[kind]
        a = (f"{k1} {place} ছিল। তার কাছে ছিল {bn(a_)}টি {thing}। {k2} এসে আরও {bn(b_)}টি দিল।\n"
             f"চলো একসঙ্গে গুনি: {bn(a_)} + {bn(b_)} = {bn(s)}।\nএখন {gen(k1)} কাছে {bn(s)}টি {thing}।\n"
             f"{k1} {bn(sub)}টি {k2}কে ফিরিয়ে দিল। এখন থাকল {bn(s)} - {bn(sub)} = {bn(s - sub)}টি।\n"
             f"প্রশ্ন: {k2} যদি আরও ২টি দেয়, তাহলে {gen(k1)} কাছে মোট কটা হবে?")
        out.append(rec("STORY", "STUDENT", u, a, {"concept_id": "m_addition", "zone_id": zone}, f"story.fln.v{kind}"))
    return out


def gen_quiz(store, rng, n, mis):
    concepts = [c for c in store["concepts"].values() if c.get("quiz_bn")]
    mis_by = {}
    for m in mis:
        mis_by.setdefault(m["concept_id"], []).append(m)
    out = []
    for i in range(n):
        c = rng.choice(concepts); qa = list(c["quiz_bn"])
        subs = [s for s in store["substitutions"].values() if s["concept_id"] == c["id"] and s.get("status") == "approved"]
        if subs:
            s = rng.choice(subs); e = store["entities"][s["local_anchor"]["entity_id"]]
            qa.append({"q": f"{gen(c['name_bn'])} একটি স্থানীয় উদাহরণ দাও।", "a": f"{e.get('name_bn', e['id'])}।"})
        for m in mis_by.get(c["id"], [])[:1]:
            qa.append({"q": f"সত্য না মিথ্যা: {m['wrong_bn']}", "a": f"মিথ্যা। {m['right_bn']}"})
        rng.shuffle(qa); qa = qa[:rng.choice([3, 3, 4])]
        us = [f"{c['name_bn']} নিয়ে {bn(len(qa))}টি ছোট প্রশ্ন বানাও, উত্তরসহ।",
              f"শ্রেণি {bn(c.get('grade', 7))}-এর জন্য {gen(c['name_bn'])} একটি ছোট কুইজ দিন, প্রতিটির উত্তরসহ।",
              f"{c['name_bn']} অধ্যায়ের ওপর {bn(len(qa))}টি প্রশ্নের একটি মূল্যায়ন-পত্র দিন, উত্তরমালা সহ।",
              f"কাল {c['name_bn']} পরীক্ষা। {bn(len(qa))}টা প্রশ্ন করে উত্তর মিলিয়ে দাও।"]
        u, k = pick(rng, us, i); target = "TEACHER" if ("দিন" in u) else "STUDENT"
        a = "\n".join(f"{bn(j + 1)}। প্রশ্ন: {x['q']}\n   উত্তর: {x['a']}" for j, x in enumerate(qa))
        out.append(rec("QUIZ_GENERATION", target, u, a, {"concept_id": c["id"]}, f"quiz.v{k}"))
    return out


def gen_lesson_plan(store, rng, n):
    out = []
    subs = [s for s in store["substitutions"].values() if s.get("status") == "approved" and check(s, store)["ok"]]
    for i in range(n):
        s = rng.choice(subs); c = store["concepts"][s["concept_id"]]; e = store["entities"][s["local_anchor"]["entity_id"]]; z = store["zones"][s["zone_id"]]
        ebn = e.get("name_bn", e["id"]); mins = rng.choice([(5, 15, 10, 5), (5, 20, 10, 5), (10, 15, 10, 5), (5, 15, 15, 5)])
        us = [f"শ্রেণি {bn(c.get('grade', 7))}-এর জন্য '{c['name_bn']}' বিষয়ে একটি পাঠ পরিকল্পনা বানান, {zname(z)} এলাকার উদাহরণ সহ।",
              f"{c['name_bn']} পড়ানোর একটি ৩৫ মিনিটের পাঠ পরিকল্পনা দিন, স্থানীয় উদাহরণ হিসেবে {ebn} ব্যবহার করে।",
              f"আগামীকাল {c['name_bn']} পড়াব। একটি পাঠ পরিকল্পনা দিন যাতে হাতে-কলমে কাজ থাকে।",
              f"{c['exam_term_bn']} বোঝানোর জন্য {ebn} দিয়ে পাঠ পরিকল্পনা তৈরি করে দিন।"]
        u, k = pick(rng, us, i)
        a = (f"বিষয়: {SUBJECT_BN.get(c.get('subject', ''), c.get('subject', ''))} · শ্রেণি: {bn(c.get('grade', 7))} · অধ্যায়: {c['name_bn']}\n"
             f"শিখন লক্ষ্য: {gen(c['exam_term_bn'])} ধারণা বোঝা এবং দৈনন্দিন জীবনে চিনতে পারা।\n"
             f"উপকরণ: পাঠ্যবই, চক-বোর্ড, {gen(ebn)} ছবি বা আসল জিনিস।\n"
             f"সূচনা ({bn(mins[0])} মিঃ): '{ebn}' নিয়ে একটি প্রশ্ন দিয়ে শুরু করুন; ছাত্রছাত্রীদের নিজের অভিজ্ঞতা বলতে দিন।\n"
             f"মূল পাঠ ({bn(mins[1])} মিঃ): {s['text_bn'].strip()}\n"
             f"হাতে-কলমে ({bn(mins[2])} মিঃ): দলে ভাগ করে {ebn} দিয়ে ঘটনাটি নিজেরা লক্ষ করা বা এঁকে দেখানো।\n"
             f"মূল্যায়ন ({bn(mins[3])} মিঃ): ৩টি ছোট প্রশ্ন; একটিতে অবশ্যই পরিভাষা '{c['exam_term_bn']}' লিখতে বলুন।\n"
             f"বাড়ির কাজ: বাড়ির আশপাশে {gen(c['name_bn'])} আর একটি উদাহরণ খুঁজে দুই লাইনে লেখা।")
        if s.get("disanalogy_flags"):
            a += "\nশিক্ষকের জন্য সতর্কতা: " + " ".join(s["disanalogy_flags"])
        out.append(rec("LESSON_PLAN", "TEACHER", u, a, {"concept_id": c["id"], "entity_id": e["id"], "zone_id": z["id"], "substitution_id": s["id"]}, f"lesson.v{k}"))
    return out


def gen_worksheet(store, rng, n):
    gens = [gen_percentage, gen_units, gen_speed, gen_area, gen_simple_interest, gen_ratio, gen_fraction, gen_multiplication, gen_money, gen_profit_loss]
    out = []
    for i in range(n):
        g = rng.choice(gens); qs = g(store, rng, 5)[:rng.choice([3, 4, 5])]
        if len(qs) < 3:
            continue
        grade = rng.choice([5, 6, 7, 8]); k = i % 3
        us = [f"শ্রেণি {bn(grade)}-এর জন্য {bn(len(qs))}টি অঙ্কের একটি অনুশীলন-পত্র বানান, স্থানীয় উদাহরণে, উত্তরমালা আলাদা করে।",
              f"বাড়ির কাজের জন্য {bn(len(qs))}টি অঙ্ক দিন, শেষে উত্তরমালা।",
              f"আমাদের এলাকার উদাহরণ দিয়ে {bn(len(qs))}টি অঙ্কের একটি ওয়ার্কশিট দিন।"][k]
        body = "\n".join(f"{bn(j + 1)}। " + q["messages"][1]["content"].replace(" ধাপে ধাপে দেখাও।", "").replace(" ধাপে ধাপে বোঝাও।", "").replace(" ধাপে ধাপে।", "") for j, q in enumerate(qs))
        keys = "\n".join(f"{bn(j + 1)}। {q['messages'][2]['content'].split('অতএব নির্ণেয় উত্তর: ')[-1]}" for j, q in enumerate(qs))
        out.append(rec("WORKSHEET_PRACTICE", "TEACHER", us, body + "\n\nউত্তরমালা:\n" + keys, {"concept_id": qs[0]["provenance"].get("concept_id")}, f"worksheet.v{k}"))
    return out


# ------------------------------------------------------------------ own teacher-checked sets from Finetune/data
def from_finetune(path, split):
    rows = []
    p = ROOT / "Finetune" / "data" / path
    if not p.exists():
        return rows
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        rows.append({"messages": r["messages"], "task_family": "GUIDED_PROBLEM_SOLVING", "instructional_target": "STUDENT",
                     "template_id": f"finetune.v3.{split}", "provenance": {"generator": "Finetune/prepare_data.py", "source": "Finetune/data v3 (teacher-checked templates)",
                                                                           "licence": "own", "validated_by": "teacher_informal", "attested_by": "AG", "date": "2026-09-19",
                                                                           "band": r.get("band"), "subject": r.get("subject"), "topic": r.get("topic")}})
    return rows


# ------------------------------------------------------------------ assembly
def digest(r):
    return hashlib.sha1("\n".join(m["content"] for m in r["messages"]).encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    rng = random.Random(a.seed); store = load_store()
    mis = (yaml.safe_load((HERE / "data" / "misconceptions_wb.yaml").read_text(encoding="utf-8")) or {}).get("misconceptions", [])
    records = []
    records += from_substitutions(store, rng) + from_misconceptions(store, rng, mis) + from_local_context(store, rng)
    records += gen_percentage(store, rng, 1800) + gen_percentage_of(store, rng, 1400) + gen_simple_interest(store, rng, 1500)
    records += gen_ratio(store, rng, 1000) + gen_units(store, rng, 2200) + gen_speed(store, rng, 1500) + gen_area(store, rng, 1500)
    records += gen_mean(store, rng, 1100) + gen_profit_loss(store, rng, 1400) + gen_fraction(store, rng, 1100) + gen_multiplication(store, rng, 1100)
    records += gen_money(store, rng, 1100) + gen_compare(store, rng, 900) + gen_calendar(store, rng, 1200)
    records += gen_fln_story(store, rng, 1700) + gen_quiz(store, rng, 2100, mis) + gen_lesson_plan(store, rng, 1800) + gen_worksheet(store, rng, 1300)
    families = {}
    for t in sorted({r["template_id"] for r in records}):
        m = TEMPLATE_RE.match(t)
        if m:
            families.setdefault(m.group(1), []).append((int(m.group(2)), t))
    eval_templates = {max(v)[1] for v in families.values() if len(v) >= 2}
    seen, per_template, kept = set(), {}, []
    for r in records:
        d = digest(r); t = r["template_id"]; cap = EVAL_CAP_PER_TEMPLATE if t in eval_templates else CAP_PER_TEMPLATE
        if d in seen or per_template.get(t, 0) >= cap:
            continue
        seen.add(d); per_template[t] = per_template.get(t, 0) + 1; kept.append(r)
    templates = sorted(per_template)
    train = [r for r in kept if r["template_id"] not in eval_templates] + from_finetune("train_v3.jsonl", "train")
    ev = [r for r in kept if r["template_id"] in eval_templates] + from_finetune("eval_real.jsonl", "eval")
    assert not ({r["template_id"] for r in train} & {r["template_id"] for r in ev}), "template overlap"
    outdir = pathlib.Path(a.out); outdir.mkdir(parents=True, exist_ok=True)
    for name, rows in (("sft_wb_v1_train.jsonl", train), ("sft_wb_v1_eval.jsonl", ev)):
        with open(outdir / name, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    allrows = train + ev; rng.shuffle(kept)
    with open(outdir / "sample_50.jsonl", "w", encoding="utf-8") as fh:
        for r in kept[:50]:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    def count(rows, key):
        c = {}
        for r in rows:
            k = r.get(key) or r["provenance"].get(key) or "-"
            c[k] = c.get(k, 0) + 1
        return dict(sorted(c.items()))
    text = "".join(m["content"] for r in kept for m in r["messages"][1:])
    bengali = sum(ch in "০১২৩৪৫৬৭৮৯" for ch in text); western = sum(ch.isdigit() and ch not in "০১২৩৪৫৬৭৮৯" for ch in text)
    leaks = [r["template_id"] for r in kept if r["task_family"] != "GUIDED_PROBLEM_SOLVING"
             and any(seg[:1] in "০১২৩৪৫৬৭৮৯" for seg in r["messages"][2]["content"].split("ধাপ ")[1:])]
    manifest = {"version": "sft_wb_v1", "seed": a.seed, "total": len(allrows), "train": len(train), "eval": len(ev), "templates": len(templates),
                "eval_templates": sorted(eval_templates), "by_task_family": count(allrows, "task_family"), "by_zone": count(allrows, "zone_id"),
                "by_target": count(allrows, "instructional_target"), "bengali_digit_share": round(bengali / max(1, bengali + western), 4),
                "step_numbering_outside_maths": len(leaks), "licence": "own", "validated_by": "teacher_informal (attested AG 2026-09-19)",
                "sha256": {n: hashlib.sha256((outdir / n).read_bytes()).hexdigest() for n in ("sft_wb_v1_train.jsonl", "sft_wb_v1_eval.jsonl")}}
    (outdir / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(json.dumps({k: manifest[k] for k in ("total", "train", "eval", "templates", "by_task_family", "by_zone", "bengali_digit_share", "step_numbering_outside_maths")}, ensure_ascii=False, indent=1))
    if leaks:
        print("WARNING: step numbering leaked outside maths:", sorted(set(leaks))[:10], file=sys.stderr); sys.exit(1)


if __name__ == "__main__":
    main()
