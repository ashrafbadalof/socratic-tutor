# Socratic Tutor

A small language model fine-tuned to teach beginner Python through the
Socratic method — asking questions instead of giving answers.

Built on Qwen2.5-0.5B with QLoRA. Constitution and behavior rules in
`config/constitution.md`.

## Status
Work in progress. See commit history for what's built so far.

## Setup

1. Create a virtual environment and activate it.
2. Install PyTorch with CUDA support (adjust CUDA version to your system):
    `pip install torch --index-url https://download.pytorch.org/whl/cu126`

3. Install the rest of the dependencies:
    `pip install -r requirements.txt`