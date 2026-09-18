import os

# Prevent CUDA memory fragmentation during weight dequantization and export
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from unsloth import FastLanguageModel


def main():
    print("Loading Qwen 3.5 4B base model and fine-tuned LoRA adapters...")

    # Load from your saved 4B adapter directory
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="QWEN3.5_4B_LORA",
        max_seq_length=2048,  # Matches the 4B training max_seq_length
        dtype=None,
        load_in_4bit=True,   # Required since adapters were trained in 4-bit
    )

    print("Enabling fast inference mode...")
    FastLanguageModel.for_inference(model)

    print("Starting GGUF conversion & quantization (q8_0)...")
    # 'q8_0' provides near 16-bit precision with minimal loss (~4.5GB file size for 4B)
    # Change quantization_method to "q4_k_m" if you need a smaller ~2.8GB file for lightweight devices
    model.save_pretrained_gguf(
        "QWEN3.5_4B_GGUF",
        tokenizer,
        quantization_method="q8_0",
    )

    print("Success! Your GGUF model has been saved to QWEN3.5_4B_GGUF/")


if __name__ == "__main__":
    main()