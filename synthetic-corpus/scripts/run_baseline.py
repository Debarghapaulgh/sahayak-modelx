#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run_baseline.py
Executes the Phase D baseline experiment by injecting local contexts
and querying gemini-2.0-flash on the 20 seed teacher prompts.
"""

import os
import sys
import json
import time
import asyncio

# Ensure we can import generate_candidate and find synthetictutor package
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BASE_DIR)
sys.path.append(ROOT_DIR)
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "scripts"))

from scripts.generate_candidate import load_locale_pack, build_context, format_system_prompt
from synthetictutor.llm.openai_client import OpenAICompatibleClient

PROMPTS_FILE = os.path.join(BASE_DIR, "prompts", "real-teacher-prompts.jsonl")
OUTPUT_FILE = os.path.join(BASE_DIR, "prompts", "baseline-results.jsonl")

async def run_single(client, prompt_item, pack, idx):
    prompt_text = prompt_item["prompt"]
    task_type = prompt_item["task_type"]
    grade = prompt_item["grade"]
    subject = prompt_item["subject"]
    
    # 1. Build Context
    context = build_context(pack, grade, subject)
    
    # 2. Format Prompt with Context
    full_prompt = format_system_prompt(context, prompt_text, task_type)
    
    # 3. Call Gemini
    print(f"[{idx+1}/20] Querying gemini-2.0-flash for Class {grade} {subject} {task_type} ... ", end="", flush=True)
    try:
        response = await client.generate_text(
            prompt=full_prompt,
            temperature=0.7,
            max_tokens=2048
        )
        print("[Success]")
        return {
            "id": f"northbengal-baseline-{idx+1:04d}",
            "context": context,
            "task_type": task_type,
            "prompt": prompt_text,
            "ideal_response": response,  # The baseline response to be reviewed/edited
            "status": "pending_review",
            "notes": "Generated during Phase D baseline experiment."
        }
    except Exception as e:
        print(f"[Failed: {e}]")
        return None

async def main():
    if not os.path.exists(PROMPTS_FILE):
        print(f"Error: {PROMPTS_FILE} not found.")
        sys.exit(1)
        
    print("Initializing local Ollama Client (sarg-base:latest)...")
    client = OpenAICompatibleClient(base_url="http://localhost:11434/v1", model_name="sarg-base:latest")
    
    try:
        pack = load_locale_pack()
    except Exception as e:
        print(f"Error loading locale pack: {e}")
        sys.exit(1)
        
    prompts = []
    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                prompts.append(json.loads(line.strip()))
                
    print(f"Loaded {len(prompts)} teacher prompts. Starting generation...\n")
    
    results = []
    for idx, prompt_item in enumerate(prompts):
        result = await run_single(client, prompt_item, pack, idx)
        if result:
            results.append(result)
        # Sleep to avoid hitting rate limits
        await asyncio.sleep(2)
        
    # Write output JSONL
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    print(f"\nBaseline run complete. Saved {len(results)} outputs to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
