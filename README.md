# SyntheticTutor 🎓🤖

**SyntheticTutor** is a research-quality, modular framework designed to generate realistic, pedagogically grounded Socratic tutoring dialogues from curriculum sources (such as NCERT and State Board textbooks). 

Rather than building a standard conversational agent, **SyntheticTutor** implements an automated synthetic data generation pipeline to fine-tune educational Large Language Models (LLMs) on Socratic tutoring strategies, misconception resolution, and Indic language education.

---

## 🌟 Key Features

- 📚 **Curriculum Ingestion**: Extract concepts, prerequisites, learning objectives, and misconceptions directly from textbook sources.
- 🕸️ **Structured Knowledge Graph**: Represent concept dependencies as a Directed Acyclic Graph (DAG) for pedagogical sequencing.
- 🎯 **Pedagogical Strategy & Persona Generator**: Formulate Socratic lesson plans aligned with Bloom's Taxonomy and simulate realistic student learning curves.
- 🤖💬 **Multi-Agent Simulation**: Autonomous Teacher and Student AI agents simulating realistic, multi-turn educational dialogues.
- ⚖️ **Multi-Judge Guardrail Suite**: Evaluate synthetic dialogues for factual accuracy, pedagogical soundness, persona consistency, and anti-leakage (preventing direct answer spoilers).
- 🇮🇳 **Indic Multilingual Support**: Translate and adapt educational dialogues into Indic languages (Hindi, Tamil, Hinglish, etc.).
- 📦 **Multi-Format SFT Exporter**: Export filtered high-quality datasets to ShareGPT, ChatML, HuggingFace Datasets, and Parquet.
- ⚡ **Scalable Async Engine**: Rate-limited, concurrent execution engine with checkpointing and state tracking.

---

## 🏗️ Architecture

```
synthetictutor/
├── core/          # Domain models (Pydantic V2) & interface protocols
├── llm/           # Provider abstractions (Gemini, OpenAI, vLLM)
├── ingestion/     # Textbook PDF/JSON parsers & concept chunkers
├── knowledge/     # Concept DAG & Knowledge Graph representation
├── planning/      # Lesson planners & student/teacher persona factory
├── simulation/    # Multi-agent Socratic dialogue runner
├── evaluation/    # Multi-judge verification suite (Factual, Pedagogical, Leakage)
├── multilingual/  # Indic language adaptation & code-switching
├── export/        # ShareGPT, ChatML & Parquet SFT exporters
└── pipeline/      # Async batch pipeline runner & CLI
```

---

## 🚀 Quickstart

```bash
# Install package in editable mode
pip install -e .

# Run sample pipeline CLI
synthetictutor run --config configs/pipeline.yaml
```
