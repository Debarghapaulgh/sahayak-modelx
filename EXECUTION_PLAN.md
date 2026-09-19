# Execution Plan — sahayak-modelx

**Objective:** West Bengal's own Bengali-medium teaching model. Today: an open Apache-2.0 Indian foundation
(30B MoE) adapted for behaviour, format and identity, grounded on the WBBSE curriculum, served on our own infra
under DPDP. Next: **local-context awareness in the weights** (wider adaptation, then continued pretraining on a
West Bengal corpus). North star: a model **built from scratch, in West Bengal, for West Bengal**, in the proposed
SARGVISION Centre for AI & Innovation (Siliguri).

_Owner key: **[C]** Abhishek+Claude · **[D]** Debargha (data engine) · **[V]** varunesh-v (eval) ·
**[S]** Sachitt (GPU jobs) · **[T]** teachers. Flow: `feature → develop → main`._

---

## Locked decisions (don't relitigate)
- **Base:** the official Apache-2.0 open Indian foundation (30B MoE). **Serve via the CHAT TEMPLATE** — raw completion
  loops. It is a **reasoning model** (`<think>`): the `enable_thinking:false` template flag is **not honoured** on our
  serving stack (verified live 2026-09-19), so direct answering must come from SFT, not a flag.
- **Knowledge for cited answers = RAG** over WBBSE textbooks. **Fine-tune (rung 3) = behaviour, format, identity,
  pedagogy** on a teacher-built corpus. **CPT (rung 4) = language, locale and curriculum *familiarity* in the weights** —
  on rights-cleared text only. _(Revised 2026-09-19: the earlier "never bake anything into weights" lock is superseded;
  facts for students still come with citations from RAG.)_
- **"Our model" today = adaptation of an open Indian model on sovereign infra.** From-scratch is the multi-year north
  star, not a current claim. _(Revised 2026-09-19.)_
- **Cost:** AWS Activate credits; teardown discipline; scale-to-zero once wired.
- **Data is the moat and the bottleneck.** See `DATA_ENGINE.md`.

---

## Workstreams
A · Serving & infra   **B · Data Engine (`DATA_ENGINE.md`)**   C · Fine-tune   D · Evaluation
E · RAG (curriculum)   F · Governance & teacher review   G · Cost & sovereignty   H · Compute access (IndiaAI / partners)

---

## The ladder — how much of the model we own
| Rung | What changes | Buys | Status |
|---|---|---|---|
| 1 | Prompt + RAG | grounded, cited answers | ✅ in use |
| 2 | Attention-only QLoRA (r=16, router frozen) | voice, format, identity | ready, needs GPU quota |
| **3** | Wider LoRA (attention + MLP/experts, low rank) + **DPO** on teacher preferences, 25% general mix | first **local knowledge + pedagogical judgement** in weights → **v1** | next |
| **4** | **CPT** on a WB corpus (0.5–2 B tokens) → re-SFT → re-DPO | vocabulary, place names, curriculum phrasing, exam style at the weight level → **v2**, not reproducible without our data | 3–6 mo |
| 5 | From scratch (Bengali-first tokenizer + pretraining) | the base itself is ours | multi-year, Siliguri CoE |

---

## Phased plan

### Phase 0 — Foundations ✅ DONE
- License cleared; base serves coherently (chat template); repo + CI + branching; honest data-prep + eval scaffolding.

### Phase 1 — Reproducible serving · [C][S]
1. ✅ One-command deploy (`Serving/deploy_endpoint.py`, lmi28 + chat template). Re-validated live 2026-09-19 with
   teaching prompts (lesson plan, quiz, worked sum, story): coherent Bengali once the `<think>` trace is stripped.
2. **Wire scale-to-zero** via inference components.
3. **File the AWS Support case** for EC2 / training GPU quota.
- **DoD:** idle cost ≈ 0; the team can invoke it.

### Phase 2 — Data Engine v1 · [D][C][V][T] — **see `DATA_ENGINE.md`**
Track 0 harden + merge PR #12 → Tracks 1–7. **DoD:** 10,000 approved records, 5 WB zones, WB-local eval, teacher sign-off.

### Phase 3 — RAG on curriculum (parallel with 2) · [C]
1. Index the 13,914 approved grounding chunks (from PR #12) with the curriculum manifest as metadata.
2. Grounded answering with citations; no ungrounded facts to students.
- **DoD:** curriculum-accurate answers with sources on the live base.

### Phase 4 — Fine-tune v1 (rung 3) · [S][C]
1. Wider QLoRA on the bf16 base: attention + MLP/expert projections at low rank; router frozen until data ≥ 10k;
   identity + ~25% general mix. Then **DPO** on teacher preference pairs (format-by-task, register, locale fit).
2. Merge → quantise → serve.
- **DoD:** format, identity, locale probes and pedagogy rubric win on the honest eval; general ability down < 5%; served.

### Phase 5 — Evaluation gate · [V][T]
- Correctness · curriculum coverage · pedagogy rubric · **local-context probes** · format compliance · safety/grounding ·
  forgetting. **DoD:** all gates pass; no hallucinated facts to children.

### Phase 6 — Pilot serve · [C][S][T]
- Fine-tuned v1 + RAG to a teacher cohort; measure real usage. **DoD:** real teachers using it; experience captured.

### Phase 7 — Continued pretraining (rung 4) → v2 · [C][S][H]
1. Assemble the CPT corpus (0.5–2 B tokens): approved chunks, public-domain Bengali literature, bn-Wikipedia (CC-BY-SA),
   WB gazettes, **licensed** textbooks. Provenance per document.
2. Compute: **IndiaAI Mission subsidised GPUs** / partner cluster / cloud (8× H100-class, days–weeks). LoRA-CPT first,
   full-parameter if budget allows. Low LR, general-data interleave, forgetting gates.
3. Re-SFT + re-DPO on the v2 base. **DoD:** local probes and curriculum phrasing improve over v1; forgetting < 5%.

### Phase 8 — Classroom distillation · [C][S]
- Distil v2 into a 3–7B model (Unsloth → GGUF) for offline / low-connectivity classrooms. **DoD:** runs on a phone-class
  device; same teaching voice; eval within an agreed margin of v2.

### Phase 9 — From scratch (rung 5) · north star
- Bengali-first tokenizer, pretraining corpus, frontier-lab compute — the Siliguri Centre. Multi-year; tracked as
  strategy, not sprint work.

---

## Critical path
`base serves ✅ → PR #12 hardened → data engine v1 ∥ RAG → rung-3 fine-tune → eval → pilot → CPT (v2) → distil`

## Rough timeline (rides on data + compute access)
| When | Milestone |
|---|---|
| Week 1 | PR #12 hardened + merged; Tracks 4, 5, 7 started; scale-to-zero; quota case filed |
| Weeks 2–6 | Data engine v1 (10k approved, 5 zones) + RAG index |
| Weeks 6–8 | Rung-3 fine-tune v1 + eval gate |
| Weeks 8–10 | Pilot with a teacher cohort |
| Months 3–6 | CPT → v2 (rights-cleared corpus; IndiaAI / partner compute) |
| Months 6–12 | Classroom distillation; termly teacher-feedback DPO |
| Multi-year | From scratch, in the Siliguri Centre |

## Risks & mitigations
| Risk | Mitigation |
|---|---|
| Secrets in a public repo (PR #12 had hardcoded keys) | rotate now; CI secret scan; env-only credentials |
| Textbook copyright for CPT | state permission via the CoE / state proposal; until then rights-cleared text only |
| API-generated records (provider ToS) | provenance field; quarantine; prefer own-model / open-model generation |
| Catastrophic forgetting under wider LoRA / CPT | general-data mix, low LR, LoRA-CPT first, forgetting gate −5% |
| MoE router collapse on small data | router frozen until ≥ 10k records; unfreeze only with eval gates |
| Training GPU quota (EC2=0) | AWS Support case; SageMaker Training Jobs; Modal; IndiaAI compute |
| Reasoning trace reaches students | SFT teaches direct answers (flag not honoured); strip `<think>` at serving |
| Data is the moat AND the bottleneck | teacher recruitment; grounded generation; Track 6 review loop |
| Idle GPU cost | scale-to-zero + mandatory teardown |

## GPU runs — process of record (set 2026-09-19 after 17 failed jobs)

What the day taught: every failure was a library/API mismatch discovered ~7 min in, after the 30B model had loaded
(~440 s of GPU each, ≈ ₹1,150 total); the one run that trained did so at ~270 tokens/s (4-bit dequant on a 128-expert
MoE + serial `device_map="auto"`), i.e. ~5% of four A10Gs, with no step checkpoint under a 3 h cap.

1. **Eval before training.** No run without the WB-local scorecard (#23) to judge it.
2. **Rehearse for free.** `Finetune/smoke_local.sh` (CPU, pinned libs, 135M model, real Sarvam config/tokenizer) must pass
   before `launch_sagemaker_training.py` will submit. It catches signatures, `token_type_ids`, the separate
   `chat_template.jinja`, wrong LoRA target names (`query_key_value`, `dense`; never `gate`) and checkpoint/resume.
3. **Iterate small, scale once.** Recipe work (format, direct answers, DPO pairs, eval calibration) on a 2–4B open
   Bengali-capable model at ~₹100/epoch; port the winning recipe to the 30B.
4. **Every job resumable and bounded.** `--save-steps` + `CheckpointConfig` (S3-synced), `MaxRuntime` sized from
   measured steps/s, `--resume-from <job>` instead of relaunching from zero.
5. **Provenance gate in code.** The launcher refuses data that is not in `DataEngine/out/MANIFEST.json`
   (`licence: own`, sha256 match) unless `--allow-unverified-data` is passed for a throwaway experiment.
6. **One slot, one protocol.** Job names carry the owner; `--stop` refuses other people's jobs; post on #28 before
   launching; `--dry-run` first; a cost line per day in `PROGRESS.md`.
7. **Fix the 30B stack next.** bf16 LoRA with FSDP/ZeRO-3 across all four GPUs (no dequant, real data parallelism) is
   expected to be 10–20× the current throughput on the same instance; one smoke test decides. Spot training quota and the
   IndiaAI Mission application cover the CPT phase; outside H100 providers are an acceptable fallback for training
   (synthetic, PII-free data), never for serving.

## Tracking
Epic issue **#3** (model) · Data Engine epic **#19** · `PROGRESS.md` = living status. This file = the plan.
