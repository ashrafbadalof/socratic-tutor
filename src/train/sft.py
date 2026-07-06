import argparse
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "data" / "sft" / "train.jsonl"
BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
SYSTEM_PROMPT_PATH = PROJECT_ROOT / "config" / "system_prompt.md"

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

    with open(SYSTEM_PROMPT_PATH, newline="", encoding="utf-8") as f:
        constitution = f.read()
    
    def add_system_message(example):
        example['messages'].insert(0, {"role":"system", "content": constitution})
        return example
    dataset = dataset.map(add_system_message)
    return dataset

def build_lora_config():
    config = LoraConfig(
        task_type='CAUSAL_LM',
        r=16,
        lora_alpha=32,
        bias="none",
        lora_dropout=0.05,
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'up_proj', 'down_proj', 'gate_proj'],
    )
    return config

def build_training_args(output_dir, smoke_test = False):
    common = dict(
        output_dir = output_dir,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        lr_scheduler_type='cosine',
        warmup_ratio=0.03,
        logging_steps=5,
        bf16=True,
        optim='paged_adamw_8bit',
        max_seq_length=1024,
        report_to='none',
        )
    if smoke_test:
        return SFTConfig(**common, num_train_epochs=1, max_steps=5, save_strategy='no')
    return SFTConfig(**common, num_train_epochs=3, save_strategy='epoch')


def train(model, tokenizer, dataset, training_args, lora_config):
    trainer = SFTTrainer(
        model = model,
        train_dataset=dataset,
        args=training_args,
        tokenizer=tokenizer,
        peft_config=lora_config,
    )
    trainer.train()
    trainer.save_model()
    return trainer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-samples", type=int, default=None,
                        help="Use only N samples (for smoke testing).")
    parser.add_argument("--output-dir", type=str, required=True,
                        help="Where to save the LoRA adapter.")
    parser.add_argument("--smoke-test", action="store_true",
                        help="Fast run for verifying the pipeline works.")
    args = parser.parse_args()

    print("main() started")
    model, tokenizer = load_model_and_tokenizer()
    dataset = load_training_dataset(DATASET_PATH, args.max_samples)
    lora_config = build_lora_config()
    training_args = build_training_args(args.output_dir, smoke_test=args.smoke_test)
    train(model, tokenizer, dataset, training_args, lora_config)
    print(f'Adapter saved to: {args.output_dir}')

if __name__ == "__main__":
    main()