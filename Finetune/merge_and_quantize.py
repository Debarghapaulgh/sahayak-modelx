#!/usr/bin/env python3
"""
merge_and_quantize.py — Phase F. Merge the LoRA adapter into the bf16 base, save merged weights,
then (separately) quantize for serving. Run on the GPU box.

Step 1 (this script): merge -> ./out/sahayak-ft-merged  (bf16 full weights)
Step 2 (quantize): pick ONE, then upload to s3://sahayak-models-aps1/sahayak-ft-v1/ and redeploy.

Usage: python merge_and_quantize.py --adapter ./out/sahayak-ft-v1 --out ./out/sahayak-ft-merged
"""
import argparse, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE = "sarvamai/Sarvam-30B"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", default="./out/sahayak-ft-v1")
    ap.add_argument("--out", default="./out/sahayak-ft-merged")
    a = ap.parse_args()

    print("loading bf16 base (full precision — merge must NOT be on the 4-bit copy)...")
    base = AutoModelForCausalLM.from_pretrained(
        BASE, torch_dtype=torch.bfloat16, device_map="cpu", trust_remote_code=True)
    print("applying + merging LoRA...")
    merged = PeftModel.from_pretrained(base, a.adapter).merge_and_unload()
    merged.save_pretrained(a.out, safe_serialization=True)
    AutoTokenizer.from_pretrained(BASE, trust_remote_code=True).save_pretrained(a.out)
    print(f"merged bf16 weights -> {a.out}")

    print("""
NEXT — quantize for serving (pick ONE, matching how you'll serve on g5/A10G):

  # compressed-tensors (matches the base's own format; use llm-compressor):
  #   pip install llmcompressor
  #   from llmcompressor.transformers import oneshot
  #   oneshot(model="%s", recipe="W4A16", output_dir="./out/sahayak-ft-w4a16")

  # or AWQ (autoawq):
  #   pip install autoawq
  #   from awq import AutoAWQForCausalLM ...  (4-bit)

Then:
  aws s3 sync ./out/sahayak-ft-<quant>/ s3://sahayak-models-aps1/sahayak-ft-v1/
  # in deploy_sahayak_30b.py: MODEL_SOURCE="s3"; S3_MODEL_PREFIX="s3://sahayak-models-aps1/sahayak-ft-v1/"
  AWS_PROFILE=sargvision .venvb/bin/python deploy_sahayak_30b.py deploy
""" % a.out)

if __name__ == "__main__":
    main()
