import os
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
import torch
from packaging.version import parse as parse_version
import trl
from datasets import load_dataset
from trl import SFTConfig, SFTTrainer

def main():
    max_seq_length = 2048
    dtype = None
    load_in_4bit = True

    model_name = "unsloth/Qwen3.5-4B"

    print(f"Loading {model_name} in 4-bit...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        dtype=dtype,
        load_in_4bit=load_in_4bit,
        device_map="cuda:0",
    )

    print("Applying LoRA adapters (Rank 16)...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=[
            "in_proj_qkv",
            "out_proj",
            "in_proj_z",
            "in_proj_b",
        ],
        lora_alpha=32,
        lora_dropout=0.0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )

    if tokenizer.chat_template is None:
        tokenizer = get_chat_template(tokenizer, chat_template="qwen-2.5")

    def format_prompts(examples):
        convs = examples["messages"]
        texts = [tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convs]
        return {"text": texts}

    full_dataset = load_dataset("json", data_files="/home/psx/Documents/finetuning/final bengal.jsonl", split="train")
    sampled_dataset = full_dataset.train_test_split(test_size=0.5, seed=3407)["train"]
    dataset = sampled_dataset.map(format_prompts, batched=True)

    max_len_kwarg = {"max_length": max_seq_length} if parse_version(trl.__version__) >= parse_version("0.16.0") else {"max_seq_length": max_seq_length}

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset,
        args=SFTConfig(
            dataset_text_field="text",
            **max_len_kwarg,
            dataset_num_proc=1,
            packing=False,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=16,
            warmup_steps=10,
            num_train_epochs=1.5,
            learning_rate=2e-5,
            lr_scheduler_type="cosine",
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=5,
            optim="adamw_8bit",
            weight_decay=0.1,
            seed=3407,
            gradient_checkpointing=True,
            output_dir="outputs",
        ),
    )

    print("Starting Qwen 3.5 4B fine-tuning...")
    trainer.train()

    model.save_pretrained("QWEN3.5_4B_LORA")
    tokenizer.save_pretrained("QWEN3.5_4B_LORA")
    print("Training complete!")

if __name__ == "__main__":
    main()