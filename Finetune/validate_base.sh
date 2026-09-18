#!/usr/bin/env bash
# validate_base.sh — sanity-check that the OFFICIAL Apache-2.0 base serves coherently.
# Run on an EC2 g5.12xlarge (Deep Learning AMI), spot is fine. ~30 min, a few $ of credits.
#
# IMPORTANT: Sarvam-30B REQUIRES the chat template — raw text completion (/v1/completions)
# produces degenerate loops ("is is is…"). So we test via /v1/chat/completions (messages),
# which applies the model's chat template. Coherent here => the base is good.
set -euo pipefail

MODEL="sarvamai/Sarvam-30B"        # official, Apache-2.0, base MoE (128 experts, top-6 routing)

python3 -m venv ~/vbase && source ~/vbase/bin/activate
pip install -U vllm                # NOTE: Sarvam recommends a specific vLLM build for full support;
                                   # if output is still degenerate, use their fork/hot-patch or try
                                   # the vLLM-listed repo sarvamai/sarvam2-30b-a3b.

echo "== serving $MODEL (bf16, TP=4) =="
vllm serve "$MODEL" --tensor-parallel-size 4 --trust-remote-code \
    --max-model-len 4096 --dtype bfloat16 &
PID=$!
sleep 300   # 30B download + load

fail=0
for uc in "What is the capital of France? Answer in one short sentence." \
          "ভারতের রাজধানীর নাম কী? সংক্ষেপে বলো।" \
          "৪০০-এর ১৫% কত? বাংলায় ধাপে ধাপে বোঝাও।"; do
  echo "=== USER: $uc ==="
  out=$(curl -s localhost:8000/v1/chat/completions -H 'Content-Type: application/json' \
        -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"$uc\"}],\"max_tokens\":256,\"temperature\":0,\"chat_template_kwargs\":{\"enable_thinking\":false}}")
  echo "$out"
  # degeneracy: same short token repeated 4+ times, or empty
  echo "$out" | grep -qiE '(\b\w+\b)( \1){3,}' && { echo ">> LOOKS DEGENERATE"; fail=1; }
  echo
done
kill $PID 2>/dev/null || true

if [ $fail -eq 0 ]; then
  echo "RESULT: PASS — official base is coherent with the chat template. Serve/fine-tune from $MODEL."
else
  echo "RESULT: DEGENERATE even with the chat template -> use Sarvam's vLLM build (fork/hot-patch),"
  echo "  or try sarvamai/sarvam2-30b-a3b, or serve via plain Transformers/TGI. Do NOT fine-tune yet."
fi
echo "DoD: you can say coherent-or-not from real chat output, not from healthy logs."
