# Socratic Tutor

A small language model fine-tuned to teach beginner Python through the
Socratic method: asking questions instead of giving answers.

Built on Qwen2.5-0.5B with QLoRA. Constitution and behavior rules in
`config/constitution.md`.

Model: [ashrafb04/socratic-tutor-v1](https://huggingface.co/ashrafb04/socratic-tutor-v1)

## What it does

Ask it "what's a for loop?" and it asks you a question back. Paste broken code and it
points at the line without fixing it.

## What it doesn't do well

- Rambles. Often 5+ questions when the constitution says at most 2.
- Weak at redirecting off-topic requests — that behavior didn't make it into the training data.
- Occasionally slips a partial definition in before the question.

## Setup

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu126
pip install -r requirements.txt
python src/demo/app.py    # Gradio chat demo
```
