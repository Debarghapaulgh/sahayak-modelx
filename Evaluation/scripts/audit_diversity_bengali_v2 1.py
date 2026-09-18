#!/usr/bin/env python3
"""
Bengali Diversity Audit v2 - dual-format support (Format A + Format B).
Dataset: JSONL with {messages: [{role:system},{role:user},{role:assistant}]}

Format A (1751 rows): [metadata: জেলা: X | শ্রেণী: Y | বিষয়/বিষয়: Z | পাঠ্য অধ্যায়: W]
Format B (444 rows):  bullet list:
  - বিষয়: X
  - শ্রেণি: Y
  - বিষয়বস্তু: W
  - অঞ্চল/জেলা: Z

v2 changes vs audit_diversity_bengali.py:
- get_field handles both pipe (|) and newline/dash (- ) delimiters
- parse_meta handles both spellings শ্রেণী/শ্রেণি, বিষয়বস্তু/পাঠ্য অধ্যায়, জেলা/অঞ্চল/জেলা
- Searches full sys_content if metadata: block missing (Format B has no [metadata:])
Same tokenizer, embeddings, stratified logic as v1.
"""
import json, re, os, sys, math, random
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np

DATA_PATH = "/Users/varunesh/Desktop/Sargvision/Validator/northbengal-sft-chat-bengali-clean.jsonl"
OUT_DIR = Path("reports_bengali")
if len(sys.argv) > 2:
    OUT_DIR = Path(sys.argv[2])
elif os.environ.get("OUT_DIR"):
    OUT_DIR = Path(os.environ["OUT_DIR"])
if len(sys.argv) > 1 and sys.argv[1] and not sys.argv[1].startswith("-"):
    DATA_PATH = sys.argv[1]
OUT_DIR.mkdir(parents=True, exist_ok=True)

EMBED_MODEL = os.environ.get("EMBED_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")

# ---------- Bengali text utils ----------
BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

def normalize_digits(s):
    return s.translate(BN_DIGITS)

def bn_tokens(s):
    s = normalize_digits(s.lower())
    return re.findall(r'[\u0980-\u09ff]+|[a-z0-9]+', s)

def tokens(s):
    return bn_tokens(s)

def hash_normalize(s):
    s = normalize_digits(s.lower())
    s = re.sub(r'[^\u0980-\u09ff\w\s]', '', s)
    return re.sub(r'\s+', ' ', s).strip()

def distinct_n(texts, n):
    ngrams = []
    for t in texts:
        toks = tokens(t)
        for i in range(len(toks) - n + 1):
            ngrams.append(tuple(toks[i:i + n]))
    if not ngrams:
        return 0.0
    return len(set(ngrams)) / len(ngrams)

def ttr(texts):
    toks = []
    for t in texts:
        toks.extend(tokens(t))
    if not toks:
        return 0
    return len(set(toks)) / len(toks)

def jaccard(a, b):
    sa, sb = set(tokens(a)), set(tokens(b))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

def pairwise_jaccard_sample(texts, n_sample=300):
    random.seed(0)
    sample = texts if len(texts) < n_sample else random.sample(texts, n_sample)
    jaccards = []
    for i in range(0, len(sample), 10):
        for j in range(i + 1, min(i + 10, len(sample))):
            jaccards.append(jaccard(sample[i], sample[j]))
    if not jaccards:
        return {"mean": 0, "p95": 0, "max": 0, "pct_gt0.8": 0, "n_pairs": 0}
    return {
        "mean": float(np.mean(jaccards)),
        "p95": float(np.percentile(jaccards, 95)),
        "max": float(np.max(jaccards)),
        "pct_gt0.8": float(np.mean([1 for x in jaccards if x > 0.8])),
        "n_pairs": len(jaccards),
    }

def entropy_of_counter(counter):
    total = sum(counter.values())
    if total == 0 or len(counter) <= 1:
        return 0.0, 0.0, 0.0
    probs = [c / total for c in counter.values()]
    ent = -sum(p * math.log2(p) for p in probs if p > 0)
    max_ent = math.log2(len(counter))
    return ent, max_ent, ent / max_ent if max_ent else 0

# ---------- Bengali metadata v2 ----------
def get_field(block, labels):
    # Try primary: label: value until pipe or newline (covers both formats)
    for lab in labels:
        # 1) pipe-terminated (Format A)
        m = re.search(re.escape(lab) + r'\s*:\s*([^|\]]+)', block)
        if m:
            v = m.group(1).strip().split("\n")[0].strip().lstrip("- ").strip()
            if v:
                return v
        # 2) newline/dash-terminated (Format B) - capture until newline or |
        m = re.search(re.escape(lab) + r'\s*:\s*([^\n|]+)', block)
        if m:
            v = m.group(1).strip().split("\n")[0].strip().lstrip("- ").strip()
            if v:
                return v
        # 3) bullet dash prefix "- lab: value"
        m = re.search(r'-\s*' + re.escape(lab) + r'\s*:\s*(.+)', block)
        if m:
            v = m.group(1).strip().split("\n")[0].strip()
            if v:
                return v
    return "UNKNOWN"

def parse_meta(sys_content):
    m = re.search(r'metadata:(.*)', sys_content, re.DOTALL)
    if m:
        block = m.group(1)
    else:
        # Format B has no [metadata:], search full content (last 1500 chars covers বিবরণী block)
        block = sys_content
    district = get_field(block, ['জেলা', 'অঞ্চল/জেলা', 'অঞ্চল'])
    klass_raw = get_field(block, ['শ্রেণী', 'শ্রেণি'])
    subject_raw = get_field(block, ['বিষয়', 'বিষয়'])
    chapter = get_field(block, ['পাঠ্য অধ্যায়', 'পাঠ্য অধ্যায়', 'বিষয়বস্তু', 'বিষয়বস্তু', 'Topic', 'Chapter'])
    return district, klass_raw, subject_raw, chapter

SUBJECT_EN = {
    'গণিত': 'Mathematics', 'ভূগোল': 'Geography', 'বিজ্ঞান': 'Science',
    'জীবন বিজ্ঞান': 'Biology', 'অর্থনীতি': 'Economics',
    'সমাজবিজ্ঞান': 'Social Science', 'রসায়ন': 'Chemistry',
    'ভৌত বিজ্ঞান': 'Physics', 'EVS': 'EVS',
}

def subject_norm(raw):
    m = re.search(r'\(([^)]+)\)', raw)
    if m:
        return m.group(1).strip()
    for bn, en in SUBJECT_EN.items():
        if bn in raw:
            return en
    return raw.strip()

CLASS_NORM = {
    '১ম': '1', '1': '1', 'প্রথম': '1',
    '২য়': '2', '2': '2', 'দ্বিতীয়': '2',
    '৩য়': '3', '3': '3', 'তৃতীয়': '3',
    '৪র্থ': '4', '4': '4', 'চতুর্থ': '4',
    '৫ম': '5', '5': '5', 'পঞ্চম': '5',
    '৬ষ্ঠ': '6', '6': '6', 'ষষ্ঠ': '6',
    '৭ম': '7', '7': '7', 'সপ্তম': '7',
    '৮ম': '8', '8': '8', 'অষ্টম': '8',
    '৯ম': '9', '9': '9', 'নবম': '9',
    '১০ম': '10', '10': '10', 'দশম': '10',
    'একাদশ': '11', '11': '11',
    'দ্বাদশ': '12', '12': '12',
}

def class_norm(raw):
    r = raw.strip()
    if r in CLASS_NORM:
        return CLASS_NORM[r]
    m = re.search(r'(\d+)', normalize_digits(r))
    if m:
        return m.group(1)
    return r

# ---------- analysis ----------
def analyze_view(name, texts):
    total = len(texts)
    uniq = len(set(hash_normalize(t) for t in texts))
    dupes = total - uniq
    lens_chars = [len(t) for t in texts]
    lens_words = [len(tokens(t)) for t in texts]
    total_tokens = sum(lens_words)
    vocab = len(set(t for txt in texts for t in tokens(txt)))
    res = {
        "count": total,
        "unique_normalized": uniq,
        "exact_duplicates": dupes,
        "duplicate_rate": dupes / total if total else 0,
        "chars": {"mean": float(np.mean(lens_chars)), "median": float(np.median(lens_chars)),
                  "std": float(np.std(lens_chars)), "min": int(np.min(lens_chars)),
                  "max": int(np.max(lens_chars)), "p95": float(np.percentile(lens_chars, 95))},
        "words": {"mean": float(np.mean(lens_words)), "median": float(np.median(lens_words)),
                  "std": float(np.std(lens_words)), "min": int(np.min(lens_words)),
                  "max": int(np.max(lens_words)), "p95": float(np.percentile(lens_words, 95))},
        "total_tokens": total_tokens,
        "vocab": vocab,
        "ttr": vocab / total_tokens if total_tokens else 0,
        "distinct_1": distinct_n(texts, 1),
        "distinct_2": distinct_n(texts, 2),
        "distinct_3": distinct_n(texts, 3),
        "jaccard_sample": pairwise_jaccard_sample(texts),
    }
    starts = Counter(t[:80].replace("\n", " | ") for t in texts)
    res["top_starts"] = [{"text": k, "count": v} for k, v in starts.most_common(5)]
    norm_map = Counter(hash_normalize(t) for t in texts)
    res["duplicate_examples"] = [{"normalized": k[:150], "count": v}
                                 for k, v in norm_map.most_common(5) if v > 1][:5]
    return res

def embedding_sim(texts, model, label=""):
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    embs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False, batch_size=64)
    sims = embs @ embs.T
    triu = np.clip(sims[np.triu_indices(len(texts), k=1)], -1, 1)
    sim = {"method": f"embedding_cosine:{EMBED_MODEL}", "mean": float(np.mean(triu)),
           "std": float(np.std(triu)), "median": float(np.median(triu)),
           "p95": float(np.percentile(triu, 95)), "p99": float(np.percentile(triu, 99)),
           "max": float(np.max(triu)), "min": float(np.min(triu)),
           "pct_gt0.80": float(np.mean(triu > 0.80)), "pct_gt0.85": float(np.mean(triu > 0.85)),
           "pct_gt0.70": float(np.mean(triu > 0.70)), "n_pairs": int(len(triu))}
    rows, cols = np.triu_indices(len(texts), k=1)
    flat_idx = np.argpartition(triu, -min(20, len(triu) - 1))[-20:]
    top_pairs = []
    for idx in flat_idx[np.argsort(triu[flat_idx])[::-1]]:
        i, j = int(rows[idx]), int(cols[idx])
        top_pairs.append({"i": i, "j": j, "score": float(triu[idx]),
                          "a_preview": texts[i][:200].replace("\n", " | "),
                          "b_preview": texts[j][:200].replace("\n", " | ")})
    sim["top_pairs"] = top_pairs
    for k in [10, 15, 20]:
        if len(texts) < k * 2:
            continue
        try:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(embs)
            sil = silhouette_score(embs, labels) if len(set(labels)) > 1 else 0
            sim[f"kmeans_k{k}"] = {"silhouette": float(sil),
                                   "cluster_sizes": dict(Counter(int(x) for x in labels))}
        except Exception as e:
            print(f"kmeans k={k} failed for {label}: {e}")
    try:
        from sklearn.decomposition import PCA
        emb2d = PCA(n_components=2).fit_transform(embs)
        np.save(OUT_DIR / f"pca2d_{label}.npy", emb2d)
        sim["pca_2d"] = True
    except Exception as e:
        print(f"PCA failed for {label}: {e}")
    return sim

def tfidf_sim(texts):
    from sklearn.feature_extraction.text import TfidfVectorizer
    vec = TfidfVectorizer(token_pattern=r'(?u)[\u0980-\u09ff\w]+', ngram_range=(1, 2), max_features=10000)
    tfidf = vec.fit_transform(texts)
    from sklearn.metrics.pairwise import cosine_similarity
    sims = cosine_similarity(tfidf)
    triu = sims[np.triu_indices(len(texts), k=1)]
    sim = {"method": "tfidf_cosine_bn", "mean": float(np.mean(triu)), "std": float(np.std(triu)),
           "median": float(np.median(triu)), "p95": float(np.percentile(triu, 95)),
           "p99": float(np.percentile(triu, 99)), "max": float(np.max(triu)),
           "pct_gt0.80": float(np.mean(triu > 0.80)), "pct_gt0.85": float(np.mean(triu > 0.85)),
           "n_pairs": int(len(triu))}
    rows, cols = np.triu_indices(len(texts), k=1)
    flat_idx = np.argpartition(triu, -min(20, len(triu) - 1))[-20:]
    top_pairs = []
    for idx in flat_idx[np.argsort(triu[flat_idx])[::-1]]:
        i, j = int(rows[idx]), int(cols[idx])
        top_pairs.append({"i": i, "j": j, "score": float(triu[idx]),
                          "a_preview": texts[i][:200].replace("\n", " | "),
                          "b_preview": texts[j][:200].replace("\n", " | ")})
    sim["top_pairs"] = top_pairs
    return sim

def load_dataset(path):
    objs = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                msgs = obj.get("messages")
                if not isinstance(msgs, list) or len(msgs) < 3:
                    print(f"warn line {i}: unexpected messages format")
                    continue
                objs.append(obj)
            except Exception as e:
                print(f"skip line {i}: {e}")
    return objs

def main():
    path = DATA_PATH
    print(f"Loading {path} ...")
    objs = load_dataset(path)
    print(f"Loaded {len(objs)} rows")
    systems = [o["messages"][0]["content"] for o in objs]
    users = [o["messages"][1]["content"] for o in objs]
    assistants = [o["messages"][2]["content"] for o in objs]

    districts, klasses, subjects, chapters = [], [], [], []
    subj_raw_c, klass_raw_c = Counter(), Counter()
    for s in systems:
        d, k_raw, sj_raw, ch = parse_meta(s)
        k, sj = class_norm(k_raw), subject_norm(sj_raw)
        districts.append(d); klasses.append(k); subjects.append(sj); chapters.append(ch)
        subj_raw_c[sj_raw] += 1; klass_raw_c[k_raw] += 1

    subj_c, klass_c, combo_c, chap_c, dist_c = (Counter(subjects), Counter(klasses),
        Counter(zip(subjects, klasses)), Counter(chapters), Counter(districts))
    chap_ent, chap_max, chap_norm = entropy_of_counter(chap_c)
    subj_ent, _, subj_norm = entropy_of_counter(subj_c)
    klass_ent, _, klass_norm = entropy_of_counter(klass_c)
    sorted_chap = sorted(chap_c.values(), reverse=True)
    top5_cover = sum(sorted_chap[:5]) / len(objs)
    top10pct = max(1, int(len(chap_c) * 0.1))
    top10pct_cover = sum(sorted_chap[:top10pct]) / len(objs)

    # embeddings availability
    model = None
    try:
        from sentence_transformers import SentenceTransformer
        print(f"Loading embedding model {EMBED_MODEL} ...")
        model = SentenceTransformer(EMBED_MODEL)
        print("Model loaded")
    except Exception as e:
        print(f"No embeddings, TF-IDF fallback: {e}")

    views = {"system": systems, "user": users, "assistant": assistants}
    light, sims = {}, {}
    for name, texts in views.items():
        print(f"\nAnalyzing {name} ...")
        light[name] = analyze_view(name, texts)
        try:
            sims[name] = embedding_sim(texts, model, label=name) if model else tfidf_sim(texts)
            print(f"{name}: mean {sims[name]['mean']:.3f} p95 {sims[name]['p95']:.3f} %>0.80 {sims[name]['pct_gt0.80']:.3%}")
        except Exception as e:
            print(f"similarity failed for {name}: {e}")
            sims[name] = {"error": str(e)}

    # stratified: per-subject + per-class on assistant texts
    def stratify(keys, key_texts, min_n_emb=50):
        out = {}
        for key in sorted(set(keys)):
            idx = [i for i, k in enumerate(keys) if k == key]
            txts = [key_texts[i] for i in idx]
            lv = analyze_view(key, txts)
            entry = {"n": len(idx), "lightweight": lv}
            try:
                if model and len(idx) >= min_n_emb:
                    e = embedding_sim(txts, model, label=f"tmp")
                    entry["sim_mean"] = e["mean"]; entry["sim_p95"] = e["p95"]
                    entry["sim_pct_gt080"] = e["pct_gt0.80"]; entry["sim_method"] = e["method"]
                else:
                    e = tfidf_sim(txts) if len(idx) >= 10 else None
                    if e:
                        entry["sim_mean"] = e["mean"]; entry["sim_p95"] = e["p95"]
                        entry["sim_pct_gt080"] = e["pct_gt0.80"]; entry["sim_method"] = e["method"]
            except Exception as ex:
                entry["sim_error"] = str(ex)
            out[str(key)] = entry
        return out

    print("\nStratifying by subject (assistant) ...")
    by_subject = stratify(subjects, assistants)
    print("Stratifying by class (assistant) ...")
    by_class = stratify(klasses, assistants)
    # combos: lightweight counts only
    by_combo = {}
    for (sj, k), n in combo_c.most_common():
        idx = [i for i in range(len(objs)) if subjects[i] == sj and klasses[i] == k]
        txts = [assistants[i] for i in idx]
        lv = analyze_view(f"{sj}|{k}", txts)
        by_combo[f"{sj}|grade_{k}"] = {"n": n, "distinct_2": lv["distinct_2"],
            "ttr": lv["ttr"], "duplicate_rate": lv["duplicate_rate"],
            "jaccard_mean": lv["jaccard_sample"]["mean"]}

    def diversity_score(lv, sim, ent_norm=None):
        mean_cos = sim.get("mean", lv["jaccard_sample"]["mean"]) if sim else lv["jaccard_sample"]["mean"]
        cos_div = 1 - max(0, min(1, mean_cos))
        ent = ent_norm if ent_norm is not None else 0.5
        return (0.35 * cos_div + 0.25 * lv["distinct_2"] + 0.2 * (1 - lv["duplicate_rate"]) + 0.2 * ent) * 100

    scores = {n: diversity_score(light[n], sims.get(n, {}), chap_norm if n == "assistant" else None) for n in views}
    summary = {
        "dataset": path, "total_rows": len(objs), "embed_model": EMBED_MODEL if model else "tfidf_fallback",
        "distributions": {
            "subjects": dict(subj_c), "subjects_raw": dict(subj_raw_c),
            "classes": dict(klass_c), "classes_raw": dict(klass_raw_c),
            "districts": dict(dist_c),
            "subject_class_combos": {f"{a}|grade_{b}": v for (a, b), v in combo_c.items()},
            "chapters_unique": len(chap_c), "chapters_top10": chap_c.most_common(10),
            "chapters_singletons": sum(1 for c in chap_c.values() if c == 1),
            "chapters_repeated": sum(1 for c in chap_c.values() if c > 1),
            "chapter_entropy": chap_ent, "chapter_max_entropy": chap_max,
            "chapter_entropy_norm": chap_norm,
            "chapter_top10pct_cover": top10pct_cover, "chapter_top5_cover": top5_cover,
            "subject_entropy_norm": subj_norm, "class_entropy_norm": klass_norm,
        },
        "views": {n: {"lightweight": light[n], "similarity": {k: v for k, v in sims.get(n, {}).items() if not k.startswith("top")},
                      "diversity_score_0_100": scores[n]} for n in views},
        "by_subject_assistant": {k: {"n": v["n"], "distinct_2": v["lightweight"]["distinct_2"],
            "ttr": v["lightweight"]["ttr"], "duplicate_rate": v["lightweight"]["duplicate_rate"],
            "jaccard_mean": v["lightweight"]["jaccard_sample"]["mean"],
            "sim_mean": v.get("sim_mean"), "sim_p95": v.get("sim_p95"),
            "sim_pct_gt080": v.get("sim_pct_gt080")} for k, v in by_subject.items()},
        "by_class_assistant": {k: {"n": v["n"], "distinct_2": v["lightweight"]["distinct_2"],
            "ttr": v["lightweight"]["ttr"], "duplicate_rate": v["lightweight"]["duplicate_rate"],
            "jaccard_mean": v["lightweight"]["jaccard_sample"]["mean"],
            "sim_mean": v.get("sim_mean"), "sim_p95": v.get("sim_p95"),
            "sim_pct_gt080": v.get("sim_pct_gt080")} for k, v in by_class.items()},
        "by_combo": by_combo,
        "overall_diversity_score": float(np.mean(list(scores.values()))),
        "notes": "Bengali-aware tokenizer (U+0980-U+09FF), digit normalization, multilingual embeddings, v2 dual-format metadata parser",
    }
    with open(OUT_DIR / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

    import csv
    for name, sim in sims.items():
        if "top_pairs" in sim:
            with open(OUT_DIR / f"pairs_to_review_{name}.csv", "w", newline='', encoding="utf-8") as cf:
                w = csv.writer(cf); w.writerow(["rank", "i", "j", "score", "a_preview", "b_preview"])
                for r, p in enumerate(sim["top_pairs"], 1):
                    w.writerow([r, p["i"], p["j"], f"{p['score']:.4f}", p["a_preview"], p["b_preview"]])
    with open(OUT_DIR / "topic_imbalance.csv", "w", newline='', encoding="utf-8") as cf:
        w = csv.writer(cf); w.writerow(["chapter", "count", "pct"])
        for t, c in chap_c.most_common():
            w.writerow([t, c, f"{c/len(objs):.3%}"])
    # subject x class matrix
    all_sj = sorted(subj_c); all_k = sorted(klass_c, key=lambda x: int(x) if x.isdigit() else 99)
    with open(OUT_DIR / "subject_class_matrix.csv", "w", newline='', encoding="utf-8") as cf:
        w = csv.writer(cf); w.writerow(["subject"] + [f"grade_{k}" for k in all_k] + ["total"])
        for sj in all_sj:
            row = [combo_c.get((sj, k), 0) for k in all_k]
            w.writerow([sj] + row + [sum(row)])
        w.writerow(["total"] + [klass_c[k] for k in all_k] + [len(objs)])
    for key, rows in [("subject", by_subject), ("class", by_class)]:
        with open(OUT_DIR / f"diversity_by_{key}.csv", "w", newline='', encoding="utf-8") as cf:
            w = csv.writer(cf)
            w.writerow([key, "n", "distinct_2", "ttr", "dup_rate", "jaccard_mean", "sim_mean", "sim_p95", "sim_pct_gt080"])
            data = by_subject if key == "subject" else by_class
            for k, v in sorted(data.items()):
                lv = v["lightweight"]
                w.writerow([k, v["n"], f"{lv['distinct_2']:.4f}", f"{lv['ttr']:.4f}",
                            f"{lv['duplicate_rate']:.4f}", f"{lv['jaccard_sample']['mean']:.4f}",
                            f"{v.get('sim_mean', 0):.4f}" if v.get("sim_mean") is not None else "",
                            f"{v.get('sim_p95', 0):.4f}" if v.get("sim_p95") is not None else "",
                            f"{v.get('sim_pct_gt080', 0):.4%}" if v.get("sim_pct_gt080") is not None else ""])
    for name, texts in views.items():
        exact = Counter(texts)
        groups = sorted([(m, c) for m, c in exact.items() if c > 1], key=lambda x: -x[1])
        with open(OUT_DIR / f"exact_duplicates_{name}.csv", "w", newline='', encoding="utf-8") as cf:
            w = csv.writer(cf); w.writerow(["group_id", "count", "message"])
            for gid, (m, c) in enumerate(groups, 1):
                w.writerow([gid, c, m[:2000]])
        print(f"{name}: exact duplicate groups {len(groups)}")

    # markdown report
    with open(OUT_DIR / "diversity_report.md", "w", encoding="utf-8") as f:
        f.write(f"# Bengali Diversity Audit v2\n\nDataset: `{path}`\nRows: {len(objs)}\n")
        f.write(f"Embeddings: `{EMBED_MODEL if model else 'tfidf_fallback'}`\n")
        f.write(f"Overall diversity: **{summary['overall_diversity_score']:.1f}/100**\n\n")
        for n in views:
            f.write(f"- {n}: {scores[n]:.1f} (sim_mean={sims.get(n, {}).get('mean', 0):.3f}, "
                    f"d2={light[n]['distinct_2']:.3f}, dup={light[n]['duplicate_rate']:.2%})\n")
        f.write(f"\nSubject entropy norm: {subj_norm:.3f}, Class entropy norm: {klass_norm:.3f}, "
                f"Chapter entropy norm: {chap_norm:.3f}\n")
        f.write(f"Chapter top5 cover: {top5_cover:.1%}, top10% cover: {top10pct_cover:.1%}, "
                f"singletons: {summary['distributions']['chapters_singletons']}/{len(chap_c)}\n\n")
        f.write("## Subject x Class (counts)\n\n| subject | " + " | ".join(f"g{k}" for k in all_k) + " | total |\n")
        f.write("|---|" + "|".join(["---"] * (len(all_k) + 2)) + "|\n")
        for sj in all_sj:
            row = [combo_c.get((sj, k), 0) for k in all_k]
            f.write(f"| {sj} | " + " | ".join(map(str, row)) + f" | {sum(row)} |\n")
        f.write("\n## Per-subject assistant diversity\n\n| subject | n | distinct_2 | dup_rate | sim_mean |\n|---|---|---|---|---|\n")
        for k in sorted(by_subject):
            v = summary["by_subject_assistant"][k]
            sm = f"{v['sim_mean']:.3f}" if v["sim_mean"] is not None else "-"
            f.write(f"| {k} | {v['n']} | {v['distinct_2']:.3f} | {v['duplicate_rate']:.2%} | {sm} |\n")
        f.write("\n## Per-class assistant diversity\n\n| class | n | distinct_2 | dup_rate | sim_mean |\n|---|---|---|---|---|\n")
        for k in sorted(by_class, key=lambda x: int(x) if x.isdigit() else 99):
            v = summary["by_class_assistant"][k]
            sm = f"{v['sim_mean']:.3f}" if v["sim_mean"] is not None else "-"
            f.write(f"| grade_{k} | {v['n']} | {v['distinct_2']:.3f} | {v['duplicate_rate']:.2%} | {sm} |\n")
    print(f"\nOverall diversity: {summary['overall_diversity_score']:.1f}/100")
    print(f"Reports saved to {OUT_DIR}/")
    return summary

if __name__ == "__main__":
    main()
