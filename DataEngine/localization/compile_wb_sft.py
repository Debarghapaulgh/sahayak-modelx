#!/usr/bin/env python3
"""Compile the West Bengal localisation store into SFT data (Tracks 3/4, #21 #22).

Every record: Bengali, WB register (teacher = আপনি, student = তুমি), Bengali digits, format by task
(numbered steps ONLY in worked maths), the canonical exam term kept, provenance attached, licence "own".
Worked sums are computed programmatically, so every number in a solution is correct by construction.
Held-out split is by TEMPLATE (a template's instances are all-train or all-eval): 0 template overlap.

    python compile_wb_sft.py            -> ../out/sft_wb_v1_{train,eval}.jsonl + MANIFEST.json + sample_50.jsonl
"""
import argparse
import hashlib
import json
import pathlib
import random
import sys

from gate import check, load_store

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent / "out"
BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
SYSTEM_BN = ("তুমি SahayakAI, পশ্চিমবঙ্গের সরকারি স্কুলের ছাত্রছাত্রী ও শিক্ষকদের জন্য বাংলা মাধ্যমের শিক্ষা-সহায়ক। "
             "গণনার প্রশ্নে ধাপে ধাপে দেখাও; অন্য সব ক্ষেত্রে সরাসরি, সংক্ষিপ্ত ও কাজের উপযোগী উত্তর দাও। সাধারণ তথ্যপ্রশ্নে "
             "ধাপ নম্বর দিও না। শিক্ষককে 'আপনি', ছাত্রছাত্রীকে 'তুমি'। সব সংখ্যা বাংলা অঙ্কে।")
EVAL_TEMPLATE_FRACTION = 0.2   # every 5th template family variant is held out
CAP_PER_TEMPLATE = 14


def bn(x):
    """Render any number/str with Bengali digits."""
    if isinstance(x, float) and x.is_integer():
        x = int(x)
    return str(x).translate(BN_DIGITS)


def rec(task, target, user, assistant, prov, template):
    sysmsg = SYSTEM_BN
    return {"messages": [{"role": "system", "content": sysmsg},
                         {"role": "user", "content": user},
                         {"role": "assistant", "content": assistant}],
            "task_family": task, "instructional_target": target, "template_id": template,
            "provenance": {"generator": "DataEngine/localization/compile_wb_sft.py", "source": "localisation store v1",
                           "licence": "own", "validated_by": "teacher_informal", "attested_by": "AG",
                           "date": "2026-09-19", **prov}}


# ------------------------------------------------------------------ substitutions -> explanations
def from_substitutions(store, rng):
    out = []
    for sid, s in store["substitutions"].items():
        if s.get("status") != "approved" or not s.get("text_bn") or not check(s, store)["ok"]:
            continue
        c = store["concepts"][s["concept_id"]]; e = store["entities"][s["local_anchor"]["entity_id"]]
        z = store["zones"][s["zone_id"]]
        prov = {"concept_id": c["id"], "entity_id": e["id"], "zone_id": z["id"], "substitution_id": sid,
                "strategy": s["strategy"]}
        zone_bn, cname, ebn, term = z.get("name_bn", z["id"]), c["name_bn"], e.get("name_bn", e["id"]), c["exam_term_bn"]
        text = s["text_bn"].strip()
        grade = c.get("grade", 6)
        # student, concept explanation with the local example
        u = rng.choice([f"{cname} কী? আমাদের {zone_bn} এলাকার উদাহরণ দিয়ে সহজভাবে বোঝাও।",
                        f"{cname} বিষয়টা {ebn} দিয়ে বুঝিয়ে দাও।",
                        f"আমি {zone_bn}-এর ছাত্র। {cname} সহজ করে বোঝাও, আমাদের চেনা উদাহরণ দিয়ে।"])
        out.append(rec("CONCEPT_EXPLANATION", "STUDENT", u, text, prov, f"sub.student.{s['strategy']}"))
        # teacher, asking for a local example to teach with (আপনি register)
        ut = rng.choice([f"শ্রেণি {bn(grade)}-এর জন্য {cname} পড়াতে {zone_bn} এলাকার একটি স্থানীয় উদাহরণ দিন।",
                         f"{cname} বোঝাতে {ebn} দিয়ে একটি ব্যাখ্যা তৈরি করে দিন, ছাত্রছাত্রীরা যেন চেনা জিনিস দিয়ে বোঝে।"])
        at = (f"আপনি {ebn} দিয়ে শুরু করতে পারেন। ছাত্রছাত্রীদের এভাবে বলা যায়:\n\n{text}\n\n"
              f"পরীক্ষার পরিভাষা অবশ্যই থাকবে: {term}। বইয়ের মূল উদাহরণটিও একবার বলে দেবেন, স্থানীয় উদাহরণ তার সঙ্গে যোগ হবে, বদলে নয়।")
        if s.get("disanalogy_flags"):
            at += "\n\nসতর্কতা:\n" + "\n".join("- " + f for f in s["disanalogy_flags"])
        out.append(rec("TEACHER_PEDAGOGY", "TEACHER", ut, at, prov, "sub.teacher.example"))
        # misconception correction from the first disanalogy flag (analogies and traps)
        if s.get("disanalogy_flags"):
            flag = s["disanalogy_flags"][0]
            um = f"{ebn} দিয়ে {cname} বোঝানো হয়, তাহলে দুটো কি একই জিনিস?"
            am = (f"ভুল ধারণা: {ebn} আর {cname} একই রকম।\nকেন ভুল: {flag}\n"
                  f"সঠিক ধারণা: {ebn} শুধু ধারণাটা চেনাতে সাহায্য করে; পরীক্ষায় ও ব্যাখ্যায় {term} শব্দটাই ব্যবহার করবে।")
            out.append(rec("MISCONCEPTION_CORRECTION", "STUDENT", um, am, prov, "sub.misconception.flag"))
    return out


# ------------------------------------------------------------------ programmatic worked sums (local context)
def worked(steps, answer_line):
    return "\n".join(steps) + f"\n\nঅতএব নির্ণেয় উত্তর: {answer_line}"


def gen_percentage(store, rng, n):
    items = [("আম", "কেজি"), ("চাল", "কেজি"), ("ইলিশ মাছ", "কেজি"), ("আলু", "কেজি"), ("চা পাতা", "কেজি"), ("সরষের তেল", "লিটার")]
    places = [("হাটে", "gangetic_plain"), ("বাজারে", "kolkata_metro"), ("মাছের আড়তে", "sundarbans_delta"), ("চা-বাগানের দোকানে", "north_bengal_tea_belt")]
    out = []
    for i in range(n):
        item, unit = rng.choice(items); place, zone = rng.choice(places)
        price = rng.choice([200, 250, 300, 400, 450, 500, 600, 800, 1200]); pct = rng.choice([5, 10, 12, 15, 20, 25, 30])
        disc = price * pct // 100; pay = price - disc
        if (price * pct) % 100:
            continue
        u = rng.choice([f"{place} {bn(price)} টাকার {item}-এ {bn(pct)}% ছাড় দিলে কত টাকা দিতে হবে? ধাপে ধাপে দেখাও।",
                        f"{item} {bn(price)} টাকা {unit}। দোকানি {bn(pct)}% ছাড় দিল। ছাড়ের টাকা ও দাম কত?"])
        a = worked([f"দেওয়া আছে: দাম {bn(price)} টাকা, ছাড় {bn(pct)}%।",
                    f"ধরি, ছাড়ের টাকা = {bn(price)} × {bn(pct)} ÷ ১০০।",
                    f"সূত্রানুসারে: {bn(price)} × {bn(pct)} ÷ ১০০ = {bn(price * pct)} ÷ ১০০ = {bn(disc)} টাকা।",
                    f"সমাধান: দিতে হবে {bn(price)} - {bn(disc)} = {bn(pay)} টাকা।"],
                   f"ছাড় {bn(disc)} টাকা, দিতে হবে {bn(pay)} টাকা।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_percentage", "zone_id": zone}, f"sum.percentage.v{i % 5}"))
    return out


def gen_simple_interest(store, rng, n):
    out = []
    for i in range(n):
        p = rng.choice([500, 1000, 1500, 2000, 2500, 4000, 5000]); r = rng.choice([4, 5, 6, 8, 10]); t = rng.choice([1, 2, 3, 4])
        if (p * r * t) % 100:
            continue
        si = p * r * t // 100; ctx = rng.choice(["হালখাতায় দোকানের ধার", "সমবায় ব্যাংকে জমা", "স্বনির্ভর গোষ্ঠীর ঋণ", "ডাকঘরে জমা"])
        u = f"{ctx}: {bn(p)} টাকা, বার্ষিক {bn(r)}% সরল সুদে {bn(t)} বছরে সুদ কত হবে? ধাপে ধাপে বোঝাও।"
        a = worked([f"দেওয়া আছে: আসল = {bn(p)} টাকা, সুদের হার = {bn(r)}%, সময় = {bn(t)} বছর।",
                    "সূত্রানুসারে: সরল সুদ = আসল × হার × সময় ÷ ১০০।",
                    f"সমাধান: {bn(p)} × {bn(r)} × {bn(t)} ÷ ১০০ = {bn(p * r * t)} ÷ ১০০ = {bn(si)} টাকা।",
                    f"সুদ-আসল = {bn(p)} + {bn(si)} = {bn(p + si)} টাকা।"], f"সুদ {bn(si)} টাকা, সুদ-আসল {bn(p + si)} টাকা।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_si", "zone_id": "gangetic_plain"}, f"sum.si.v{i % 4}"))
    return out


def gen_ratio(store, rng, n):
    out = []
    for i in range(n):
        a_, b_ = rng.choice([(3, 1), (2, 1), (4, 1), (3, 2), (5, 2)]); k = rng.choice([2, 3, 4, 5, 6, 8, 10])
        rice = a_ * k; dal = b_ * k; students = rng.choice([40, 60, 80, 100, 120])
        u = rng.choice([f"মিড-ডে মিলের খিচুড়িতে চাল ও ডালের অনুপাত {bn(a_)} : {bn(b_)}। {bn(rice)} কেজি চালের সঙ্গে কত কেজি ডাল লাগবে? ধাপে ধাপে দেখাও।",
                        f"স্কুলে {bn(students)} জন ছাত্রের খিচুড়িতে চাল : ডাল = {bn(a_)} : {bn(b_)} রাখতে হবে। {bn(rice)} কেজি চাল থাকলে ডাল কত?"])
        a = worked([f"দেওয়া আছে: চাল : ডাল = {bn(a_)} : {bn(b_)}, চাল = {bn(rice)} কেজি।",
                    f"ধরি, ডাল = x কেজি। তাহলে {bn(a_)} : {bn(b_)} = {bn(rice)} : x।",
                    f"সূত্রানুসারে: {bn(a_)} × x = {bn(b_)} × {bn(rice)}, অর্থাৎ x = {bn(b_ * rice)} ÷ {bn(a_)} = {bn(dal)}।"],
                   f"{bn(dal)} কেজি ডাল লাগবে।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_ratio", "zone_id": "rarh_plateau", "entity_id": "midday_meal"}, f"sum.ratio.v{i % 4}"))
    return out


def gen_unit_bigha(store, rng, n):
    out = []
    for i in range(n):
        b = rng.randint(1, 6); k = rng.choice([0, 5, 8, 10, 12, 15]); total = b * 20 + k
        crop = rng.choice(["ধান", "আলু", "সরষে", "পাট"])
        u = rng.choice([f"{bn(b)} বিঘা {bn(k)} কাঠা জমিতে {crop} চাষ হবে। মোট কত কাঠা? (১ বিঘা = ২০ কাঠা) ধাপে ধাপে দেখাও।",
                        f"একজন চাষির {bn(b)} বিঘা {bn(k)} কাঠা জমি। কাঠায় প্রকাশ করো।"])
        a = worked([f"দেওয়া আছে: {bn(b)} বিঘা {bn(k)} কাঠা; ১ বিঘা = ২০ কাঠা।",
                    f"সূত্রানুসারে: {bn(b)} বিঘা = {bn(b)} × ২০ = {bn(b * 20)} কাঠা।",
                    f"সমাধান: মোট = {bn(b * 20)} + {bn(k)} = {bn(total)} কাঠা।"], f"{bn(total)} কাঠা।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_unitconv", "zone_id": "rarh_plateau", "entity_id": "bigha_katha"}, f"sum.bigha.v{i % 3}"))
    return out


def gen_speed(store, rng, n):
    vehicles = [("টোটো", 20, "north_bengal_tea_belt"), ("সাইকেল", 12, "gangetic_plain"), ("মেট্রো", 45, "kolkata_metro"), ("লঞ্চ", 15, "sundarbans_delta"), ("ট্রাম", 18, "kolkata_metro")]
    out = []
    for i in range(n):
        v, speed, zone = rng.choice(vehicles); t = rng.choice([1, 2, 3, 4]); d = speed * t
        u = rng.choice([f"একটি {v} {bn(speed)} কিমি/ঘণ্টা বেগে {bn(t)} ঘণ্টা চললে কত দূর যাবে? ধাপে ধাপে দেখাও।",
                        f"{v}-র গতিবেগ {bn(speed)} কিমি/ঘণ্টা। {bn(d)} কিমি যেতে কত সময় লাগবে?"])
        if "কত দূর" in u:
            a = worked([f"দেওয়া আছে: গতিবেগ = {bn(speed)} কিমি/ঘণ্টা, সময় = {bn(t)} ঘণ্টা।",
                        "সূত্রানুসারে: দূরত্ব = গতিবেগ × সময়।",
                        f"সমাধান: {bn(speed)} × {bn(t)} = {bn(d)} কিমি।"], f"{bn(d)} কিমি।")
        else:
            a = worked([f"দেওয়া আছে: গতিবেগ = {bn(speed)} কিমি/ঘণ্টা, দূরত্ব = {bn(d)} কিমি।",
                        "সূত্রানুসারে: সময় = দূরত্ব ÷ গতিবেগ।",
                        f"সমাধান: {bn(d)} ÷ {bn(speed)} = {bn(t)} ঘণ্টা।"], f"{bn(t)} ঘণ্টা।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_speed", "zone_id": zone}, f"sum.speed.v{i % 4}"))
    return out


def gen_area(store, rng, n):
    out = []
    for i in range(n):
        L = rng.choice([20, 25, 30, 40, 50, 60]); W = rng.choice([10, 12, 15, 20, 25, 30])
        if W >= L:
            W = L // 2
        thing = rng.choice(["পুকুর", "ধানখেত", "স্কুলের মাঠ", "চা-বাগানের একটি অংশ"])
        u = f"একটি আয়তাকার {thing} {bn(L)} মিটার লম্বা ও {bn(W)} মিটার চওড়া। এর পরিসীমা ও ক্ষেত্রফল কত? ধাপে ধাপে দেখাও।"
        a = worked([f"দেওয়া আছে: দৈর্ঘ্য = {bn(L)} মি, প্রস্থ = {bn(W)} মি।",
                    f"সূত্রানুসারে: পরিসীমা = ২ × (দৈর্ঘ্য + প্রস্থ) = ২ × ({bn(L)} + {bn(W)}) = ২ × {bn(L + W)} = {bn(2 * (L + W))} মি।",
                    f"ক্ষেত্রফল = দৈর্ঘ্য × প্রস্থ = {bn(L)} × {bn(W)} = {bn(L * W)} বর্গমিটার।"],
                   f"পরিসীমা {bn(2 * (L + W))} মিটার, ক্ষেত্রফল {bn(L * W)} বর্গমিটার।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_area", "zone_id": "gangetic_plain"}, f"sum.area.v{i % 3}"))
    return out


def gen_mean(store, rng, n):
    out = []
    for i in range(n):
        k = rng.choice([4, 5, 6]); vals = [rng.randint(18, 32) for _ in range(k)]
        while sum(vals) % k:
            vals[-1] += 1
        mean = sum(vals) // k; ctx = rng.choice(["এক চা-শ্রমিকের দৈনিক পাতা তোলা (কেজি)", "এক সপ্তাহের হাটে বিক্রি (কেজি)", "পাঁচ দিনের বৃষ্টি (মিমি)"])
        vs = ", ".join(bn(v) for v in vals)
        u = f"{ctx}: {vs}। গড় কত? ধাপে ধাপে দেখাও।"
        a = worked([f"দেওয়া আছে: রাশিগুলি {vs}; রাশির সংখ্যা {bn(k)}।",
                    f"সূত্রানুসারে: গড় = রাশিগুলির যোগফল ÷ রাশির সংখ্যা।",
                    f"সমাধান: যোগফল = {bn(sum(vals))}; গড় = {bn(sum(vals))} ÷ {bn(k)} = {bn(mean)}।"], f"গড় {bn(mean)}।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_mean", "zone_id": "north_bengal_tea_belt"}, f"sum.mean.v{i % 3}"))
    return out


def gen_profit_loss(store, rng, n):
    out = []
    for i in range(n):
        item, zone = rng.choice([("ইলিশ", "sundarbans_delta"), ("আলু", "gangetic_plain"), ("আম", "north_bengal_tea_belt"), ("কাজু", "medinipur_coastal")])
        cp = rng.choice([40, 60, 80, 100, 150, 200, 400, 600]); delta = rng.choice([-30, -20, -10, 10, 20, 40, 50]); sp = cp + delta
        if sp <= 0:
            continue
        u = f"এক বিক্রেতা {item} প্রতি কেজি {bn(cp)} টাকায় কিনে {bn(sp)} টাকায় বেচলেন। লাভ না ক্ষতি, কত? ধাপে ধাপে দেখাও।"
        kind = "লাভ" if delta > 0 else "ক্ষতি"
        a = worked([f"দেওয়া আছে: ক্রয়মূল্য = {bn(cp)} টাকা, বিক্রয়মূল্য = {bn(sp)} টাকা।",
                    ("সূত্রানুসারে: বিক্রয়মূল্য > ক্রয়মূল্য হলে লাভ = বিক্রয়মূল্য - ক্রয়মূল্য।" if delta > 0 else
                     "সূত্রানুসারে: ক্রয়মূল্য > বিক্রয়মূল্য হলে ক্ষতি = ক্রয়মূল্য - বিক্রয়মূল্য।"),
                    f"সমাধান: {bn(max(cp, sp))} - {bn(min(cp, sp))} = {bn(abs(delta))} টাকা।"], f"প্রতি কেজিতে {kind} {bn(abs(delta))} টাকা।")
        out.append(rec("GUIDED_PROBLEM_SOLVING", "STUDENT", u, a, {"concept_id": "m_profitloss", "zone_id": zone}, f"sum.pl.v{i % 3}"))
    return out


# ------------------------------------------------------------------ FLN stories, quizzes, lesson plans, worksheets
def gen_fln_story(store, rng, n):
    kids = ["মিতু", "রাজু", "রিনা", "সুমন", "পিয়ালী", "বাবলু", "টুম্পা", "সোনালি"]
    things = [("আম", "north_bengal_tea_belt"), ("মুড়ির মোয়া", "gangetic_plain"), ("নারকেল", "sundarbans_delta"), ("কাঁঠালের কোয়া", "rarh_plateau"), ("লাল ফুল", "gangetic_plain"), ("ঘুড়ি", "kolkata_metro")]
    out = []
    for i in range(n):
        a_, b_ = rng.randint(1, 9), rng.randint(1, 9); k1, k2 = rng.sample(kids, 2); thing, zone = rng.choice(things)
        s = a_ + b_; sub = rng.randint(1, s)
        u = rng.choice([f"দ্বিতীয় শ্রেণির জন্য একটি ছোট গল্প লেখো যাতে যোগ ({bn(a_)} + {bn(b_)}) শেখানো যায়।",
                        f"ছোটদের জন্য {thing} দিয়ে যোগ-বিয়োগের একটা গল্প বানাও।"])
        a = (f"{k1}-র কাছে ছিল {bn(a_)}টি {thing}। {k2} এসে আরও {bn(b_)}টি দিল।\n"
             f"চলো একসঙ্গে গুনি: {bn(a_)} + {bn(b_)} = {bn(s)}।\nএখন {k1}-র কাছে {bn(s)}টি {thing}।\n"
             f"{k1} {bn(sub)}টি খেয়ে ফেলল। এখন থাকল {bn(s)} - {bn(sub)} = {bn(s - sub)}টি।\n"
             f"প্রশ্ন: {k2} যদি আরও {bn(2)}টি দেয়, তাহলে মোট কটা হবে?")
        out.append(rec("STORY", "STUDENT", u, a, {"concept_id": "m_addition", "zone_id": zone}, f"story.fln.v{i % 4}"))
    return out


def gen_quiz(store, rng, n):
    concepts = [c for c in store["concepts"].values() if c.get("quiz_bn")]
    out = []
    for i in range(n):
        c = rng.choice(concepts)
        # concept's own Q/A + one local-example question from an approved substitution of this concept
        qa = list(c["quiz_bn"])
        subs = [s for s in store["substitutions"].values() if s["concept_id"] == c["id"] and s.get("status") == "approved"]
        if subs:
            s = rng.choice(subs); e = store["entities"][s["local_anchor"]["entity_id"]]
            qa.append({"q": f"{c['name_bn']}-এর একটি স্থানীয় উদাহরণ দাও।", "a": f"{e.get('name_bn', e['id'])}।"})
        rng.shuffle(qa); qa = qa[:3]
        u = rng.choice([f"{c['name_bn']} নিয়ে {bn(len(qa))}টি ছোট প্রশ্ন বানাও, উত্তরসহ।",
                        f"শ্রেণি {bn(c.get('grade', 7))}-এর জন্য {c['name_bn']}-এর একটি ছোট কুইজ দিন, প্রতিটির উত্তরসহ।"])
        target = "TEACHER" if "দিন" in u else "STUDENT"
        a = "\n".join(f"{bn(j + 1)}। প্রশ্ন: {x['q']}\n   উত্তর: {x['a']}" for j, x in enumerate(qa))
        out.append(rec("QUIZ_GENERATION", target, u, a, {"concept_id": c["id"]}, f"quiz.v{i % 3}"))
    return out


def gen_lesson_plan(store, rng, n):
    out = []
    subs = [s for s in store["substitutions"].values() if s.get("status") == "approved" and check(s, store)["ok"]]
    for i in range(n):
        s = rng.choice(subs); c = store["concepts"][s["concept_id"]]; e = store["entities"][s["local_anchor"]["entity_id"]]; z = store["zones"][s["zone_id"]]
        ebn = e.get("name_bn", e["id"]); mins = rng.choice([(5, 15, 10, 5), (5, 20, 10, 5), (10, 15, 10, 5)])
        u = rng.choice([f"শ্রেণি {bn(c.get('grade', 7))}-এর জন্য '{c['name_bn']}' বিষয়ে একটি পাঠ পরিকল্পনা বানান, {z.get('name_bn', '')} এলাকার উদাহরণ সহ।",
                        f"{c['name_bn']} পড়ানোর একটি ৩৫ মিনিটের পাঠ পরিকল্পনা দিন, স্থানীয় উদাহরণ হিসেবে {ebn} ব্যবহার করে।"])
        a = (f"বিষয়: {c.get('subject', '')} · শ্রেণি: {bn(c.get('grade', 7))} · অধ্যায়: {c['name_bn']}\n"
             f"শিখন লক্ষ্য: {c['exam_term_bn']}-এর ধারণা বোঝা এবং দৈনন্দিন জীবনে চিনতে পারা।\n"
             f"উপকরণ: পাঠ্যবই, চক-বোর্ড, {ebn}-এর ছবি বা আসল জিনিস।\n"
             f"সূচনা ({bn(mins[0])} মিঃ): '{ebn}' নিয়ে একটি প্রশ্ন দিয়ে শুরু করুন; ছাত্রছাত্রীদের নিজের অভিজ্ঞতা বলতে দিন।\n"
             f"মূল পাঠ ({bn(mins[1])} মিঃ): {s['text_bn'].strip()}\n"
             f"হাতে-কলমে ({bn(mins[2])} মিঃ): দলে ভাগ করে {ebn} দিয়ে ঘটনাটি নিজেরা লক্ষ করা বা এঁকে দেখানো।\n"
             f"মূল্যায়ন ({bn(mins[3])} মিঃ): ৩টি ছোট প্রশ্ন; একটিতে অবশ্যই পরিভাষা '{c['exam_term_bn']}' লিখতে বলুন।\n"
             f"বাড়ির কাজ: বাড়ির আশপাশে {c['name_bn']}-এর আর একটি উদাহরণ খুঁজে দুই লাইনে লেখা।")
        if s.get("disanalogy_flags"):
            a += "\nশিক্ষকের জন্য সতর্কতা: " + " ".join(s["disanalogy_flags"])
        out.append(rec("LESSON_PLAN", "TEACHER", u, a, {"concept_id": c["id"], "entity_id": e["id"], "zone_id": z["id"], "substitution_id": s["id"]}, f"lesson.v{i % 3}"))
    return out


def gen_worksheet(store, rng, n):
    out = []
    for i in range(n):
        gens = [gen_percentage, gen_unit_bigha, gen_speed, gen_area]
        g = rng.choice(gens); qs = g(store, rng, 4)
        if len(qs) < 3:
            continue
        u = f"শ্রেণি ৭-এর জন্য {bn(len(qs))}টি অঙ্কের একটি অনুশীলন-পত্র বানান, স্থানীয় উদাহরণে, উত্তরমালা আলাদা করে।"
        body = "\n".join(f"{bn(j + 1)}। {q['messages'][1]['content'].replace(' ধাপে ধাপে দেখাও।', '').replace(' ধাপে ধাপে বোঝাও।', '')}" for j, q in enumerate(qs))
        keys = "\n".join(f"{bn(j + 1)}। {q['messages'][2]['content'].split('অতএব নির্ণেয় উত্তর: ')[-1]}" for j, q in enumerate(qs))
        out.append(rec("WORKSHEET_PRACTICE", "TEACHER", u, body + "\n\nউত্তরমালা:\n" + keys, {"concept_id": qs[0]["provenance"].get("concept_id")}, f"worksheet.v{i % 2}"))
    return out


# ------------------------------------------------------------------ assembly
def digest(r):
    return hashlib.sha1("\n".join(m["content"] for m in r["messages"]).encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    rng = random.Random(a.seed); store = load_store()
    records = []
    records += from_substitutions(store, rng)
    records += gen_percentage(store, rng, 60) + gen_simple_interest(store, rng, 40) + gen_ratio(store, rng, 40)
    records += gen_unit_bigha(store, rng, 30) + gen_speed(store, rng, 40) + gen_area(store, rng, 30)
    records += gen_mean(store, rng, 30) + gen_profit_loss(store, rng, 30)
    records += gen_fln_story(store, rng, 50) + gen_quiz(store, rng, 80) + gen_lesson_plan(store, rng, 60) + gen_worksheet(store, rng, 20)
    # dedup, cap per template, template-level held-out split
    seen, per_template, kept = set(), {}, []
    for r in records:
        d = digest(r)
        if d in seen or per_template.get(r["template_id"], 0) >= CAP_PER_TEMPLATE:
            continue
        seen.add(d); per_template[r["template_id"]] = per_template.get(r["template_id"], 0) + 1; kept.append(r)
    templates = sorted(per_template); eval_templates = {t for t in templates if int(hashlib.md5(t.encode()).hexdigest(), 16) % 5 == 0}
    train = [r for r in kept if r["template_id"] not in eval_templates]; ev = [r for r in kept if r["template_id"] in eval_templates]
    assert not ({r["template_id"] for r in train} & {r["template_id"] for r in ev}), "template overlap"
    outdir = pathlib.Path(a.out); outdir.mkdir(parents=True, exist_ok=True)
    for name, rows in (("sft_wb_v1_train.jsonl", train), ("sft_wb_v1_eval.jsonl", ev)):
        with open(outdir / name, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    rng.shuffle(kept)
    with open(outdir / "sample_50.jsonl", "w", encoding="utf-8") as fh:
        for r in kept[:50]:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    def count(rows, key):
        c = {}
        for r in rows:
            k = r.get(key) or r["provenance"].get(key) or "-"
            c[k] = c.get(k, 0) + 1
        return dict(sorted(c.items()))
    digits = "".join(m["content"] for r in kept for m in r["messages"][1:])
    bengali = sum(ch in "০১২৩৪৫৬৭৮৯" for ch in digits); western = sum(ch.isdigit() and ch not in "০১২৩৪৫৬৭৮৯" for ch in digits)
    steps_outside = sum(1 for r in kept if r["task_family"] != "GUIDED_PROBLEM_SOLVING" and "ধাপ " in r["messages"][2]["content"] and any(ch in "০১২৩৪৫৬৭৮৯" for ch in r["messages"][2]["content"].split("ধাপ ")[1][:2]))
    manifest = {"version": "sft_wb_v1", "seed": a.seed, "train": len(train), "eval": len(ev), "templates": len(templates),
                "eval_templates": sorted(eval_templates), "by_task_family": count(kept, "task_family"),
                "by_zone": count(kept, "zone_id"), "by_target": count(kept, "instructional_target"),
                "bengali_digit_share": round(bengali / max(1, bengali + western), 4),
                "step_numbering_outside_maths": steps_outside, "licence": "own", "validated_by": "teacher_informal (attested AG 2026-09-19)",
                "sha256": {n: hashlib.sha256((outdir / n).read_bytes()).hexdigest() for n in ("sft_wb_v1_train.jsonl", "sft_wb_v1_eval.jsonl")}}
    (outdir / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(json.dumps({k: manifest[k] for k in ("train", "eval", "templates", "by_task_family", "by_zone", "bengali_digit_share", "step_numbering_outside_maths")}, ensure_ascii=False, indent=1))
    if steps_outside:
        print("WARNING: step numbering leaked outside maths", file=sys.stderr); sys.exit(1)


if __name__ == "__main__":
    main()
