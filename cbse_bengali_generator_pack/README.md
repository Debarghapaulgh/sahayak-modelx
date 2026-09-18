# SahayakAI — CBSE Bengali Dataset Generator Pack (Qwen / Gemini / OpenAI / Groq)

This package contains everything required for any AI Assistant or developer to reproduce and generate the **CBSE / NCERT Bengali Medium SFT Chat Dataset** (`northbengal-sft-chat-bengali-clean.jsonl`) in the exact format, schema, system prompt, and grammatical precision as SahayakAI.

---

## 🔑 Qwen & Multi-Provider API Support

This generator features native support for **Qwen (Alibaba Cloud ModelStudio / DashScope International)** as well as Gemini, OpenAI, Groq, and OpenRouter.

Keys starting with `sk-ws-` are automatically detected as **Qwen (Alibaba Cloud ModelStudio International)** API keys!

### Running with Qwen:
```bash
python generate_cbse_bengali_dataset.py --provider qwen --api-key "sk-ws-H.DDRPRMM..." --model qwen-plus
```

Supported Qwen Models:
- `qwen-plus` (Default, recommended for fast structured transcreation)
- `qwen-turbo`
- `qwen-max`
- `qwen2.5-72b-instruct`

---

## 📦 What's Inside

1. **`SYSTEM_PROMPT_SPEC.md`**: Detailed specification for system prompts, district mappings, grade ordinals, subject titles, and Bengali grammar rules.
2. **`generate_cbse_bengali_dataset.py`**: Standalone Python code with native Qwen & multi-provider REST handlers, prompt templates, pydantic schema, and automated grammar post-processing.
3. **`sample_input_candidates.jsonl`**: Sample seed records in English (CBSE NCERT).
4. **`sample_output_chat.jsonl`**: Expected ground truth SFT Chat output in pure Bengali script.
