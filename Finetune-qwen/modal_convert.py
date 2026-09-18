import modal

# We use the same image environment
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "cmake", "build-essential") # Added build tools required by llama.cpp
    .pip_install(
        "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git",
        "datasets",
        "peft",
        "bitsandbytes",
        "torchvision",
    )
)

app = modal.App("qwen-gguf-converter")
volume = modal.Volume.from_name("qwen-finetune-storage")

@app.function(
    image=image,
    gpu="A10G", 
    timeout=3600,
    volumes={"/data": volume},
)
def convert_to_gguf():
    from unsloth import FastLanguageModel
    
    print("Loading base model and LoRA adapters from volume...")
    # Load in 16-bit (False) so the merge is mathematically accurate before quantization
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="/data/QWEN3.5_9B_LORA", 
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=False, 
    )
    
    export_prefix = "/data/Qwen3.5-9B-Bengal"
    print("Starting GGUF conversion (this will merge the weights and quantize)...")
    
    # "q4_k_m" is the community gold standard for balance between size and intelligence
    model.save_pretrained_gguf(
        export_prefix, 
        tokenizer, 
        quantization_method="q4_k_m",
    )
    
    print("GGUF Conversion complete!")
    print("Check your volume for the .gguf file.")

@app.local_entrypoint()
def main():
    convert_to_gguf.remote()