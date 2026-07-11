from pathlib import Path
import gradio as gr
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from peft import PeftModel
import json
from accelerate import Accelerator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_PROMPT_PATH = PROJECT_ROOT / "config" / "system_prompt.md"

BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
ADAPTER = "ashrafb04/socratic-tutor-v1"

MAX_NEW_TOKENS = 80
TEMPERATURE = 0.5
TOP_P = 0.9
REPETITION_PENALTY = 1.15

def load_model_and_tokenizer():
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base = AutoModelForCausalLM.from_pretrained(BASE_MODEL, device_map = "auto", dtype=torch.float16)
    model = PeftModel.from_pretrained(base, ADAPTER)
    model.eval()
    return model, tokenizer

def load_system_prompt():
    with open(SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
        system_prmpt = f.read()
    return system_prmpt

def normalize_content(msg):
    content = msg["content"]
    if isinstance(content, list):
        text_parts = [
            block["text"] for block in content
            if isinstance(block, dict) and block.get("type" == "text")
        ]
        return {"role": msg["role"], "content": " ".join(text_parts)}
    return msg

def generate_response(model, tokenizer, system_prompt, chat_history, user_message):
    messages = [
        {
            "role":"system",
            "content":system_prompt,
        }
    ]
    messages.extend(normalize_content(msg) for msg in chat_history)
    messages.append({
        "role":"user",
        "content":user_message,
    })
    tokenized_chat = tokenizer.apply_chat_template(messages, add_generation_prompt = True, 
                                                   tokenize = False)
    inputs = tokenizer(tokenized_chat, return_tensors="pt").to(model.device)
    output = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, temperature=TEMPERATURE, top_p = TOP_P, repetition_penalty = REPETITION_PENALTY)
    new_tokens = output[0][inputs["input_ids"].shape[1]:]
    decoded_output = tokenizer.decode(new_tokens, skip_special_tokens = True)
    return decoded_output


def build_interface(model, tokenizer, system_prompt):
    def chat_fn(message, history):
        return generate_response(model, tokenizer, system_prompt, history, message)
    demo = gr.ChatInterface(fn=chat_fn, title = "Socratic Python Tutor",
                            examples=["What is a for loop?","What does it mean to assign a variable?","How do I create a list in Python?"],
                            description="Socratic tutor is for beginner Python programmers. Its goal is not to give answers, but to help the student arrive at answers themselves through guided questioning."
                            )
    return demo


def main():
    print('Loading model...')
    model, tokenizer = load_model_and_tokenizer()
    system_prompt = load_system_prompt()
    
    print('Building interface')
    demo = build_interface(model, tokenizer, system_prompt)

    print('Launching...')
    demo.launch(share=True)

if __name__ == "__main__":
    main()