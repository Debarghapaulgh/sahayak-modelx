#!/usr/bin/env bash
# validate_base.sh — THE decisive test. Answers: is the degenerate output the model, or the
# third-party re-quant? Serves the OFFICIAL Apache-2.0 base and checks for coherent output.
# Run on an EC2 g5.12xlarge (Deep Learning AMI), spot is fine. ~30 min, a few $ of credits.
#
# If outputs are coherent here -> the official base is good; mastersubhajit re-quant was the
# problem. Serve AND fine-tune from sarvamai/Sarvam-30B, and this whole blocker is closed.
set -euo pipefail

MODEL="sarvamai/Sarvam-30B"        # official, Apache-2.0, base MoE (128 experts, top-6, ~2.4B active)

python3 -m venv ~/vbase && source ~/vbase/bin/activate
pip install -U vllm

echo "== serving $MODEL (bf16, TP=4) =="
vllm serve "$MODEL" --tensor-parallel-size 4 --trust-remote-code \
    --max-model-len 4096 --dtype bfloat16 &
PID=$!
sleep 300   # 30B download + load

fail=0
for p in "The capital of France is" \
         "ভারতের রাজধানী হল" \
         "প্রশ্ন: ৪০০-এর ১৫% কত?\nউত্তর:"; do
  echo "=== PROMPT: $p ==="
  out=$(curl -s localhost:8000/v1/completions -H 'Content-Type: application/json' \
        -d "{\"model\":\"$MODEL\",\"prompt\":\"$p\",\"max_tokens\":48,\"temperature\":0}")
  echo "$out"
  # crude degeneracy check: same short token repeated 4+ times
  echo "$out" | grep -qiE '(\b\w+\b)( \1){3,}' && { echo ">> LOOKS DEGENERATE"; fail=1; }
  echo
done
kill $PID 2>/dev/null || true

if [ $fail -eq 0 ]; then
  echo "RESULT: PASS — official base is coherent. Blocker was the third-party re-quant."
  echo "  -> point deploy_sahayak_30b.py HF_MODEL_REPO at sarvamai/Sarvam-30B (or an OFFICIAL quant),"
  echo "     and fine-tune from sarvamai/Sarvam-30B (train_qlora.py already does)."
else
  echo "RESULT: DEGENERATE even on the official base -> it's the vLLM compressed-tensors/MoE"
  echo "  kernel path, not the checkpoint. Retry with --enforce-eager, or an official FP8/GGUF build,"
  echo "  or raise it with Sarvam. Do NOT fine-tune until the base serves cleanly."
fi
echo "DoD: you can say which of the two it was, from real output — not from healthy logs."
