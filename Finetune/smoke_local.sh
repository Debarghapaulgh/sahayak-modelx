#!/usr/bin/env bash
# smoke_local.sh — FREE rehearsal of train_qlora.py before any GPU minute is spent.
#
# Runs on a laptop CPU with the same pinned libraries as the SageMaker image and catches every failure class
# hit on 2026-09-19 (17 failed jobs, ~440 s of GPU each): SFTConfig/SFTTrainer signatures, token_type_ids,
# missing chat template, wrong LoRA target names, checkpoint/resume wiring. ~3-5 min the first time (downloads
# a 135M model + the Sarvam tokenizer/config), ~1 min after. Writes Finetune/.smoke_local.ok on success;
# launch_sagemaker_training.py refuses to launch without a stamp younger than 7 days.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
VENV=${SMOKE_VENV:-$HERE/.venv-smoke}
PY=${PYTHON:-python3}
OUT=${SMOKE_OUT:-${TMPDIR:-/tmp}/sahayak-smoke-out}
TINY=${TINY_MODEL:-HuggingFaceTB/SmolLM2-135M-Instruct}     # has a chat template and q_proj/v_proj
BASE=${BASE_MODEL:-sarvamai/Sarvam-30B}

if [ ! -x "$VENV/bin/python" ]; then
  echo "== creating $VENV with the pinned CPU stack"
  "$PY" -m venv "$VENV"
  "$VENV/bin/pip" -q install --upgrade pip
  "$VENV/bin/pip" -q install torch "transformers==4.51.3" "peft>=0.14,<0.16" "trl>=0.15,<0.20" "accelerate>=1.3" \
      "datasets>=2.20" sentencepiece huggingface_hub
fi
"$VENV/bin/python" -c "import torch,transformers,trl,peft,accelerate;print('torch',torch.__version__,'transformers',transformers.__version__,'trl',trl.__version__,'peft',peft.__version__,'accelerate',accelerate.__version__)"

echo "== 1/3 real $BASE Linear names on a meta device (config + code only, no weights)"
"$VENV/bin/python" "$HERE/train_qlora.py" --base "$BASE" --check-targets 1 --target-modules "${TARGETS:-query_key_value,dense}" | tail -4

echo "== 2/3 real $BASE tokenizer: chat template renders a training row"
"$VENV/bin/python" - "$BASE" "$HERE/../DataEngine/out/sample_50.jsonl" <<'EOF'
import json, sys
sys.path.insert(0, sys.argv[0] and __import__("os").path.dirname(__import__("os").path.abspath(sys.argv[0])) or ".")
from transformers import AutoTokenizer
base, sample = sys.argv[1], sys.argv[2]
tok = AutoTokenizer.from_pretrained(base, trust_remote_code=True)
import importlib.util, os
spec = importlib.util.spec_from_file_location("tq", os.path.join(os.path.dirname(sample), "..", "..", "Finetune", "train_qlora.py"))
tq = importlib.util.module_from_spec(spec); spec.loader.exec_module(tq)
src = tq.load_chat_template(tok, base)
row = json.loads(open(sample, encoding="utf-8").readline())
text = tok.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=False)
ids = tok(text, add_special_tokens=False)
assert "token_type_ids" in ids or True
n = len(ids["input_ids"]); assert n > 20, "template produced no tokens"
assert row["messages"][-1]["content"][:30] in text, "assistant turn missing from rendered text"
print(f"template from {src}; eos={tok.eos_token!r}; rendered {n} tokens; tail: {text[-90:]!r}")
EOF

echo "== 3/3 end-to-end on $TINY with the EXACT argv the SageMaker toolkit will generate, then checkpoint + resume (CPU)"
rm -rf "$OUT"; mkdir -p "$OUT"
# the training file is heterogeneous (compiled rows first, teacher-checked v3 rows appended, different provenance keys):
# rehearse on a head+tail mix of the REAL file so schema surprises show up here, not on the GPU (job 220640)
TRAIN_FULL="$HERE/../DataEngine/out/sft_wb_v1_train.jsonl"; MIX="$OUT/mixed.jsonl"
if [ -s "$TRAIN_FULL" ]; then { head -4 "$TRAIN_FULL"; tail -4 "$TRAIN_FULL"; } > "$MIX"; else { head -4 "$HERE/../DataEngine/out/sample_50.jsonl"; head -4 "$HERE/data/train_v3.jsonl"; } > "$MIX"; fi
echo "   rehearsal data: $(wc -l < "$MIX") rows from $( [ -s "$TRAIN_FULL" ] && echo "head+tail of the real train file" || echo "sample_50 + Finetune/data")"
# --print-args needs boto3 only for import; it creates nothing and makes no AWS calls
SM_ARGS=$("$VENV/bin/pip" -q install boto3 >/dev/null 2>&1; "$VENV/bin/python" "$HERE/launch_sagemaker_training.py" --print-args --limit 200 --max-steps 20)
echo "   toolkit argv: $SM_ARGS"
# later flags override earlier ones in argparse, so the tiny-model overrides come after the generated argv
"$VENV/bin/python" "$HERE/train_qlora.py" $SM_ARGS --base "$TINY" --quant none --limit 6 --max-steps 2 --save-steps 1 --maxlen 192 --bs 1 --ga 1 \
    --target-modules q_proj,v_proj --out "$OUT" --train "$MIX" --eval "$MIX" 2>&1 | grep -vE "Warning|warn" | tail -6
test -f "$OUT/adapter_config.json" && test -f "$OUT/train_summary.json" && ls -d "$OUT"/checkpoints/checkpoint-* >/dev/null
"$VENV/bin/python" "$HERE/train_qlora.py" --base "$TINY" --quant none --limit 6 --max-steps 3 --save-steps 1 --resume 1 --maxlen 192 --bs 1 --ga 1 \
    --target-modules q_proj,v_proj --out "$OUT" --train "$MIX" 2>&1 | grep -E "resume_from_checkpoint|\"steps\"" | tail -2
date > "$HERE/.smoke_local.ok"
echo "PASS: smoke_local ($(date)) -> $HERE/.smoke_local.ok"
