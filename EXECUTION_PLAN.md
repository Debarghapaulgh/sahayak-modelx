# Execution Plan — sahayak-modelx

**Objective:** a sovereign, Bengali-medium teaching model for West Bengal government schools —
the official Apache-2.0 **Sarvam-30B**, adapted for behaviour/format/identity and grounded on the
**WBBSE** curriculum (facts via RAG), served on Indian infra under DPDP.

_Owner key: **[C]** Abhishek+Claude (code/data/RAG/review/infra) · **[S]** Sachitt (GPU jobs) ·
**[T]** teachers (content review, real questions). Flow: `feature → develop → main`._

---

## Locked decisions (don't relitigate)
- **Base:** `sarvamai/Sarvam-30B` (Apache-2.0, 30B MoE). **Serve via the CHAT TEMPLATE** (chat
  completions / messages) — raw completion loops. It's a **reasoning model** (`<think>`).
- **Knowledge = RAG** over WBBSE textbooks. **Fine-tune = behaviour/format/identity only** — do
  NOT bake curriculum facts into weights.
- **"Our model" = adaptation of an Indian open model on sovereign infra**, not from-scratch.
- **Cost:** AWS Activate credits; teardown discipline; scale-to-zero once wired.

---

## Workstreams
A · Serving & infra   B · Data (diverse Bengali)   C · Fine-tune   D · Evaluation
E · RAG (curriculum)   F · Governance & teacher review   G · Cost & sovereignty

---

## Phased plan

### Phase 0 — Foundations ✅ DONE
- License cleared (Apache-2.0); base serves coherently (chat template); repo + CI + branching;
  honest data-prep + eval scaffolding.
- **DoD:** base serves; `feature→develop→main` enforced. **✅**

### Phase 1 — Reproducible serving (this week) · [C][S]
1. Document + commit the working serve config (chat template, LMI env, image) — `Serving/`.
2. **Wire scale-to-zero** via inference components (kill idle g5 cost).
3. **File the AWS Support case** for EC2/training GPU quota (G on-demand + spot → 48).
4. Decide **thinking vs concise** posture (suppress `<think>` via template flag or shape via SFT).
- **DoD:** one command serves the base correctly; idle cost ≈ 0; the team can invoke it.

### Phase 2 — Diverse dataset v1 · [C][S][T]
1. Build the **coverage matrix** (board × grade × subject × chapter).
2. **Grounded generation** from WBBSE text across the 7 diversity axes (see `Evaluation/`).
3. **Diversity gates**: embedding-dedup, self-BLEU, coverage %, template cap.
4. **Honest held-out eval** (0% template overlap) + a slice of **real student questions**.
5. **Teacher review** of a per-(grade×subject) sample.
- **DoD:** dataset passes diversity gates; eval is genuinely held out; teachers sign off a sample.

### Phase 3 — RAG on curriculum (parallel with 2) · [C]
1. Ingest WBBSE textbooks; build the retrieval index (findNearest).
2. Grounded answering with citations; no ungrounded facts to students.
- **DoD:** curriculum-accurate answers with sources on the live base.

### Phase 4 — Fine-tune v1 · [S]
1. QLoRA on the **bf16 base** (router frozen) + identity + ~25% general mix.
2. Merge → quantize → serve.
- **DoD:** format + identity win on the honest eval; general ability down < 5%; served.

### Phase 5 — Evaluation gate · [S][T]
- Four evals, teacher-validated: correctness, curriculum coverage, pedagogy rubric, **safety/grounding**.
- **DoD:** all gates pass; no hallucinated facts to children.

### Phase 6 — Pilot serve · [C][S][T]
- Serve the fine-tuned model + RAG to a small teacher cohort; measure **real usage**, not happy-path.
- **DoD:** real teachers using it; measured experience captured.

---

## Critical path & the real bottleneck
`base serves ✅ → (data v1 ∥ RAG) → fine-tune → eval → pilot`

Compute is cheap (credits, hours). **The binding constraints are (a) DATA + teacher review and
(b) training-GPU quota.** Model work is not the long pole — data is.

## Rough timeline (rides on data + funding)
| Week | Milestone |
|---|---|
| 1 | Serving reproducible + scale-to-zero; quota support case filed |
| 2–4 | Diverse dataset v1 + RAG index |
| 4–5 | Fine-tune v1 + eval gate |
| 6 | Pilot with a teacher cohort |

## Risks & mitigations
| Risk | Mitigation |
|---|---|
| Training GPU quota (EC2=0, self-serve rejected) | AWS Support case; SageMaker Training Jobs as fallback |
| g5 capacity flaky in Mumbai | retry windows; a non-PII validation region if needed |
| Reasoning `<think>` traces reach students | suppress via chat-template flag or SFT to the step format |
| Data is the moat AND the bottleneck | teacher recruitment + funding; grounded generation to scale |
| 30B too costly at pilot scale | distil to a 3–7B after v1 |
| Idle GPU cost | scale-to-zero + mandatory teardown (STATUS.md log) |

## Tracking
Epic issue **#3**; per-phase issues as work starts. `PROGRESS.md` = living status. This file = the plan.
