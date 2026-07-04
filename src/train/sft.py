import argparse
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig
from datasets import load_dataset
from trl import SFTTrainer


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "data" / "sft" / "train.jsonl"
BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
CONSTITUTION_PATH = PROJECT_ROOT / "config" / "constitution.md"

def load_model_and_tokenizer():
    config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, quantization_config = config)

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token

    return model, tokenizer

def load_training_dataset(path, max_samples=None):
    dataset = load_dataset(
        "json",
        data_files=str(path)
    )['train']
    if max_samples is not None:
        dataset = dataset.select(range(max_samples))

    with open(CONSTITUTION_PATH, newline="", encoding="utf-8") as f:
        constitution = f.read()
    
    def add_system_message(example):
        example['messages'].insert(0, {"role":"system", "content": constitution})
        return example
    dataset = dataset.map(add_system_message)
    return dataset




def main():
    print("main() started")
    model, tokenizer = load_model_and_tokenizer()
    dataset = load_training_dataset(DATASET_PATH, 2)
    print(dataset)

if __name__ == "__main__":
    main()