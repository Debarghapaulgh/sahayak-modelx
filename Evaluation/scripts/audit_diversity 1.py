#!/usr/bin/env python3
"""
Diversity Audit - Triple view (system/user/assistant), embeddings-first with TF-IDF fallback
Dataset: JSONL with {messages: [{role:system},{role:user},{role:assistant}]}
"""
import json, re, os, sys, math, hashlib, random, itertools
from pathlib import Path
from collections import Counter
import statistics
import numpy as np

DATA_PATH = "/Users/varunesh/Desktop/Sargvision/northbengal-sft-chat.jsonl"
OUT_DIR = Path("reports_northbengal")
# Allow override via second arg or OUT_DIR env
if len(sys.argv) > 2:
    OUT_DIR = Path(sys.argv[2])
elif os.environ.get("OUT_DIR"):
    OUT_DIR = Path(os.environ["OUT_DIR"])
OUT_DIR.mkdir(parents=True, exist_ok=True)

def load_dataset(path):
    objs=[]
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f,1):
            line=line.strip()
            if not line: continue
            try:
                obj=json.loads(line)
                msgs=obj.get("messages")
                if not isinstance(msgs, list) or len(msgs)<3:
                    print(f"warn line {i}: unexpected messages format")
                    continue
                objs.append(obj)
            except Exception as e:
                print(f"skip line {i}: {e}")
    return objs

def extract_context_field(sys_content, field):
    m=re.search(rf"{field}:\s*([^|\n]+)", sys_content, re.IGNORECASE)
    return m.group(1).strip() if m else "UNKNOWN"

def extract_topic(sys_content):
    m=re.search(r"topic:\s*(.*?)\s*\nstate:", sys_content, re.DOTALL)
    if m:
        return m.group(1).strip()
    return extract_context_field(sys_content, "topic")

def tokens(s):
    return re.findall(r"\b\w+\b", s.lower())

def distinct_n(texts, n):
    ngrams=[]
    for t in texts:
        toks=tokens(t)
        for i in range(len(toks)-n+1):
            ngrams.append(tuple(toks[i:i+n]))
    if not ngrams: return 0.0
    return len(set(ngrams))/len(ngrams)

def ttr(texts):
    toks=[]
    for t in texts:
        toks.extend(tokens(t))
    if not toks: return 0
    return len(set(toks))/len(toks)

def jaccard(a,b):
    sa=set(tokens(a)); sb=set(tokens(b))
    if not sa or not sb: return 0.0
    return len(sa&sb)/len(sa|sb)

def hash_normalize(s):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", s.lower())).strip()

def pairwise_jaccard_sample(texts, n_sample=300, pairs_per_anchor=10):
    random.seed(0)
    if len(texts) < n_sample:
        sample=texts
    else:
        sample=random.sample(texts, n_sample)
    jaccards=[]
    for i in range(0, len(sample), 10):
        for j in range(i+1, min(i+10, len(sample))):
            jaccards.append(jaccard(sample[i], sample[j]))
    if not jaccards:
        return {"mean":0,"p95":0,"max":0,"pct_gt0.8":0}
    jaccards_sorted=sorted(jaccards)
    return {
        "mean": float(np.mean(jaccards)),
        "p95": float(np.percentile(jaccards,95)),
        "max": float(np.max(jaccards)),
        "pct_gt0.8": float(np.mean([1 for x in jaccards if x>0.8])),
        "n_pairs": len(jaccards)
    }

def entropy_of_counter(counter):
    total=sum(counter.values())
    probs=[c/total for c in counter.values()]
    ent=-sum(p*math.log2(p) for p in probs if p>0)
    max_ent=math.log2(len(counter)) if len(counter)>1 else 0
    return ent, max_ent, ent/max_ent if max_ent else 0

# Lightweight per-view stats
def analyze_view(name, texts):
    total=len(texts)
    uniq=len(set(hash_normalize(t) for t in texts))
    dupes=total-uniq
    lens_chars=[len(t) for t in texts]
    lens_words=[len(tokens(t)) for t in texts]
    total_tokens=sum(lens_words)
    vocab=len(set(t for txt in texts for t in tokens(txt)))
    res={
        "count": total,
        "unique_normalized": uniq,
        "exact_duplicates": dupes,
        "duplicate_rate": dupes/total if total else 0,
        "chars": {"mean": float(np.mean(lens_chars)), "median": float(np.median(lens_chars)), "std": float(np.std(lens_chars)), "min": int(np.min(lens_chars)), "max": int(np.max(lens_chars)), "p95": float(np.percentile(lens_chars,95))},
        "words": {"mean": float(np.mean(lens_words)), "median": float(np.median(lens_words)), "std": float(np.std(lens_words)), "min": int(np.min(lens_words)), "max": int(np.max(lens_words)), "p95": float(np.percentile(lens_words,95))},
        "total_tokens": total_tokens,
        "vocab": vocab,
        "ttr": vocab/total_tokens if total_tokens else 0,
        "distinct_1": distinct_n(texts,1),
        "distinct_2": distinct_n(texts,2),
        "distinct_3": distinct_n(texts,3),
        "jaccard_sample": pairwise_jaccard_sample(texts),
    }
    # Most common starts / templates
    starts=Counter(t[:80].replace("\n"," | ") for t in texts)
    res["top_starts"]=[{"text":k, "count":v} for k,v in starts.most_common(5)]
    # Exact duplicate examples
    norm_map=Counter(hash_normalize(t) for t in texts)
    dup_examples=[{"normalized":k,"count":v} for k,v in norm_map.most_common(5) if v>1]
    res["duplicate_examples"]=dup_examples[:5]
    return res

def main():
    path=DATA_PATH
    if len(sys.argv)>1:
        path=sys.argv[1]
    print(f"Loading {path} ...")
    objs=load_dataset(path)
    print(f"Loaded {len(objs)} rows")

    systems=[o["messages"][0]["content"] for o in objs]
    users=[o["messages"][1]["content"] for o in objs]
    assistants=[o["messages"][2]["content"] for o in objs]
    # Correctly extract contextual block after the second CONTEXT marker: "\nCONTEXT\n" delimiter
    contexts=[]
    for s in systems:
        if "\nCONTEXT\n" in s:
            contexts.append(s.split("\nCONTEXT\n", 1)[1])
        elif "CONTEXT" in s:
            # fallback: take after last occurrence of CONTEXT
            contexts.append(s.rsplit("CONTEXT", 1)[1])
        else:
            contexts.append(s)

    # Parse structured fields from system
    grades=Counter(); subjects=Counter(); topics=Counter(); districts=Counter(); terrains=Counter(); settings=Counter()
    combos=Counter()
    for s in systems:
        grade=extract_context_field(s,"grade")
        subject=extract_context_field(s,"subject")
        topic=extract_topic(s)
        district=extract_context_field(s,"district")
        terrain=extract_context_field(s,"terrain")
        setting=extract_context_field(s,"setting")
        # district may contain terrain due to newline, clean
        district=district.split("\n")[0].strip()
        terrain=terrain.split("\n")[0].strip()
        grades[grade]+=1; subjects[subject]+=1; topics[topic]+=1; districts[district]+=1; terrains[terrain]+=1; settings[setting]+=1
        combos[(subject,grade)]+=1

    topic_ent, topic_max, topic_norm = entropy_of_counter(topics)
    sorted_topic_counts=sorted(topics.values(), reverse=True)
    top10pct=int(len(topics)*0.1)
    top10_cover=sum(sorted_topic_counts[:top10pct])/len(objs) if top10pct else 0
    top5_cover=sum(sorted_topic_counts[:5])/len(objs)

    # Try embeddings
    embedding_available=False
    umap_available=False
    sklearn_available=False
    try:
        from sentence_transformers import SentenceTransformer
        embedding_available=True
    except ImportError:
        print("sentence-transformers not available, TF-IDF fallback will be used")
    try:
        import sklearn
        sklearn_available=True
    except ImportError:
        print("scikit-learn not available, similarity will be Jaccard only")
    try:
        import umap
        umap_available=True
    except ImportError:
        pass

    model=None
    if embedding_available:
        try:
            print("Loading embedding model all-MiniLM-L6-v2 ...")
            from sentence_transformers import SentenceTransformer
            model=SentenceTransformer('all-MiniLM-L6-v2')
            print("Model loaded")
        except Exception as e:
            print(f"Failed to load model: {e}")
            embedding_available=False
            model=None

    # Analyze each view lightweight
    views={
        "system_context": contexts,
        "user": users,
        "assistant": assistants,
    }
    light_results={}
    for name, texts in views.items():
        print(f"\nAnalyzing {name} ...")
        light_results[name]=analyze_view(name, texts)

    # Embedding / TF-IDF similarity per view
    sim_results={}
    for name, texts in views.items():
        print(f"\nSimilarity for {name} ({len(texts)} texts)...")
        sim={}
        if embedding_available and model is not None:
            try:
                import numpy as np
                from sklearn.metrics.pairwise import cosine_similarity
                from sklearn.cluster import KMeans
                from sklearn.metrics import silhouette_score
                # Encode in batches
                embs=model.encode(texts, normalize_embeddings=True, show_progress_bar=True, batch_size=64)
                # cosine = embs @ embs.T (since normalized)
                # For 2002, full matrix 2002^2 ~4M floats ok (~32MB), compute directly
                # Use sampling for histogram to avoid O(n^2) memory peak if needed, but 2002 is fine
                sims=embs @ embs.T
                # Extract upper triangle without diagonal
                triu=sims[np.triu_indices(len(texts), k=1)]
                # Clip to [-1,1] due float error
                triu=np.clip(triu, -1, 1)
                sim["method"]="embedding_cosine"
                sim["mean"]=float(np.mean(triu))
                sim["std"]=float(np.std(triu))
                sim["median"]=float(np.median(triu))
                sim["p95"]=float(np.percentile(triu,95))
                sim["p99"]=float(np.percentile(triu,99))
                sim["max"]=float(np.max(triu))
                sim["min"]=float(np.min(triu))
                sim["pct_gt0.80"]=float(np.mean(triu>0.80))
                sim["pct_gt0.85"]=float(np.mean(triu>0.85))
                sim["pct_gt0.70"]=float(np.mean(triu>0.70))
                sim["n_pairs"]=int(len(triu))
                # Top pairs
                # Find top 20 pairs indices
                # Use argpartition for efficiency
                flat_idx=np.argpartition(triu, -20)[-20:]
                # Map flat idx to (i,j)
                # Need to reconstruct upper triangle indices
                rows, cols = np.triu_indices(len(texts), k=1)
                top_pairs=[]
                for idx in flat_idx[np.argsort(triu[flat_idx])[::-1]]:
                    i=int(rows[idx]); j=int(cols[idx])
                    top_pairs.append({"i":i,"j":j,"score":float(triu[idx]), "a_preview": texts[i][:200].replace("\n"," | "), "b_preview": texts[j][:200].replace("\n"," | ")})
                sim["top_pairs"]=top_pairs
                # Clustering
                for k in [10,15,20]:
                    try:
                        km=KMeans(n_clusters=k, random_state=42, n_init=10)
                        labels=km.fit_predict(embs)
                        sil=silhouette_score(embs, labels) if len(set(labels))>1 else 0
                        # intra/inter
                        # Compute centroids already in km.cluster_centers_
                        # Intra = mean distance to centroid, inter = mean centroid pairwise distance
                        from sklearn.metrics.pairwise import euclidean_distances
                        # intra
                        intra=[]
                        for idx, lab in enumerate(labels):
                            centroid=km.cluster_centers_[lab]
                            d=np.linalg.norm(embs[idx]-centroid)
                            intra.append(d)
                        intra_mean=float(np.mean(intra))
                        # inter
                        cent_dists=euclidean_distances(km.cluster_centers_)
                        inter_vals=cent_dists[np.triu_indices(k,1)]
                        inter_mean=float(np.mean(inter_vals)) if len(inter_vals) else 0
                        sim[f"kmeans_k{k}"]={"silhouette": float(sil), "intra_mean": intra_mean, "inter_mean": inter_mean, "cluster_sizes": Counter(labels.tolist())}
                    except Exception as e:
                        print(f"kmeans k={k} failed: {e}")
                # UMAP
                if umap_available:
                    try:
                        import umap
                        reducer=umap.UMAP(n_components=2, random_state=42)
                        emb2d=reducer.fit_transform(embs)
                        # Save plot per view later
                        sim["umap_2d"]=emb2d.tolist()  # will be used for plotting, but not dumped to json fully? keep sampled
                        # Save to file for plotting
                        np.save(OUT_DIR / f"umap_{name}.npy", emb2d)
                    except Exception as e:
                        print(f"UMAP failed for {name}: {e}")
                else:
                    # Try TSNE fallback or PCA
                    try:
                        from sklearn.decomposition import PCA
                        pca=PCA(n_components=2)
                        emb2d=pca.fit_transform(embs)
                        np.save(OUT_DIR / f"umap_{name}.npy", emb2d)
                        sim["pca_2d"]=True
                    except Exception as e:
                        print(f"PCA fallback failed: {e}")
                sim_results[name]=sim
                print(f"{name} embedding mean {sim['mean']:.3f} p95 {sim['p95']:.3f} pct>0.80 {sim['pct_gt0.80']:.3%}")
            except Exception as e:
                print(f"embedding similarity failed for {name}: {e}")
                import traceback; traceback.print_exc()
                sim_results[name]={"error": str(e)}
        elif sklearn_available:
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                from sklearn.metrics.pairwise import cosine_similarity
                vec=TfidfVectorizer(stop_words="english", ngram_range=(1,2), max_features=10000)
                tfidf=vec.fit_transform(texts)
                sims=cosine_similarity(tfidf)
                triu=sims[np.triu_indices(len(texts), k=1)]
                sim["method"]="tfidf_cosine"
                sim["mean"]=float(np.mean(triu))
                sim["std"]=float(np.std(triu))
                sim["median"]=float(np.median(triu))
                sim["p95"]=float(np.percentile(triu,95))
                sim["p99"]=float(np.percentile(triu,99))
                sim["max"]=float(np.max(triu))
                sim["pct_gt0.80"]=float(np.mean(triu>0.80))
                sim["pct_gt0.85"]=float(np.mean(triu>0.85))
                sim["n_pairs"]=int(len(triu))
                rows, cols = np.triu_indices(len(texts), k=1)
                flat_idx=np.argpartition(triu, -20)[-20:]
                top_pairs=[]
                for idx in flat_idx[np.argsort(triu[flat_idx])[::-1]]:
                    i=int(rows[idx]); j=int(cols[idx])
                    top_pairs.append({"i":i,"j":j,"score":float(triu[idx]), "a_preview": texts[i][:200].replace("\n"," | "), "b_preview": texts[j][:200].replace("\n"," | ")})
                sim["top_pairs"]=top_pairs
                sim_results[name]=sim
                print(f"{name} TF-IDF mean {sim['mean']:.3f} p95 {sim['p95']:.3f}")
            except Exception as e:
                print(f"TF-IDF failed for {name}: {e}")
                sim_results[name]={"error": str(e), "fallback_jaccard": light_results[name]["jaccard_sample"]}
        else:
            sim_results[name]={"method":"jaccard_only", "jaccard": light_results[name]["jaccard_sample"]}

    # Structured distributions
    dist={
        "grades": dict(grades),
        "subjects": dict(subjects),
        "districts": dict(districts),
        "terrains": dict(terrains),
        "settings": dict(settings),
        "topics_unique": len(topics),
        "topics_top10": topics.most_common(10),
        "topics_singletons": sum(1 for c in topics.values() if c==1),
        "topics_repeated": sum(1 for c in topics.values() if c>1),
        "topic_entropy": topic_ent,
        "topic_max_entropy": topic_max,
        "topic_entropy_norm": topic_norm,
        "topic_top10pct_cover": top10_cover,
        "topic_top5_cover": top5_cover,
        "grade_subject_combos": {f"{k[0]}_grade_{k[1]}": v for k,v in combos.items()},
    }

    # Diversity scores per view: 0.3*(1-mean_cosine) +0.2*distinct2 +0.2*(1-duplicate_rate)+0.3*entropy_norm (only for topics, else 0.5)
    # For per-view, use view-specific mean cosine if available else jaccard mean
    def diversity_score(light, sim, entropy_norm=None):
        if sim and "mean" in sim:
            mean_cos=sim["mean"]
        else:
            # fallback jaccard mean
            mean_cos=light["jaccard_sample"]["mean"]
        d2=light["distinct_2"]
        dup=light["duplicate_rate"]
        # normalize mean_cos 0-1 (cosine 0 diverse, 1 redundant) so 1-mean is diversity
        cos_div=1 - max(0, min(1, mean_cos))
        ent = entropy_norm if entropy_norm is not None else 0.5
        score=0.35*cos_div + 0.25*d2 + 0.2*(1-dup) + 0.2*ent
        return score*100

    scores={}
    for name in views:
        ent = topic_norm if name=="assistant" else 0.5  # only assistant/user reflect topic, but use generic
        scores[name]= diversity_score(light_results[name], sim_results.get(name,{}), ent if name=="system_context" else None)

    summary={
        "dataset": path,
        "total_rows": len(objs),
        "distributions": dist,
        "views": {
            name: {
                "lightweight": light_results[name],
                "similarity": sim_results.get(name, {}),
                "diversity_score_0_100": scores[name]
            } for name in views
        },
        "overall_diversity_score": float(np.mean(list(scores.values()))),
        "notes": "EVS passage treated as single topic (129 rows), triple view, embeddings-first"
    }
    # Save json
    with open(OUT_DIR/"summary.json","w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    # Save csv of top pairs per view
    import csv
    for name, sim in sim_results.items():
        if "top_pairs" in sim:
            with open(OUT_DIR/f"pairs_to_review_{name}.csv","w", newline='', encoding="utf-8") as cf:
                w=csv.writer(cf)
                w.writerow(["rank","i","j","score","a_preview","b_preview"])
                for rank, p in enumerate(sim["top_pairs"],1):
                    w.writerow([rank, p["i"], p["j"], f"{p['score']:.4f}", p["a_preview"], p["b_preview"]])
    # Save topic imbalance csv
    with open(OUT_DIR/"topic_imbalance.csv","w", newline='', encoding="utf-8") as cf:
        w=csv.writer(cf)
        w.writerow(["topic","count","pct"])
        for t,c in topics.most_common():
            w.writerow([t,c,f"{c/len(objs):.3%}"])
    # Exact duplicates for all three views - byte-for-byte identical
    for name, texts in views.items():
        exact_counter = Counter(texts)
        dup_groups = [(msg,cnt, [i for i, t in enumerate(texts) if t == msg]) for msg,cnt in exact_counter.items() if cnt > 1]
        dup_groups.sort(key=lambda x: -x[1])
        with open(OUT_DIR/f"exact_duplicates_{name}.csv","w", newline='', encoding="utf-8") as cf:
            w=csv.writer(cf)
            w.writerow(["group_id","count","indices","message"])
            for gid, (msg,cnt,idxs) in enumerate(dup_groups,1):
                w.writerow([gid, cnt, ";".join(map(str, idxs)), msg])
        # Also normalized duplicates reference
        norm_counter = Counter(hash_normalize(t) for t in texts)
        norm_dupes = sum(1 for c in norm_counter.values() if c>1)
        print(f"{name}: exact duplicate groups {len(dup_groups)}, normalized groups {norm_dupes}")

    print(f"\n=== SUMMARY ===")
    print(f"Overall diversity score: {summary['overall_diversity_score']:.1f}/100")
    for k,v in scores.items():
        print(f" {k}: {v:.1f}")
    print(f"Topic entropy {topic_ent:.2f}/{topic_max:.2f} ({topic_norm:.1%})")
    print(f"Reports saved to {OUT_DIR}/")
    return summary

if __name__=="__main__":
    main()
