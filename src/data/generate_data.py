import os
import json
from dotenv import load_dotenv
import argparse
from openai import OpenAI
from pathlib import Path

load_dotenv()
client = OpenAI()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONSTITUTION_PATH = PROJECT_ROOT / "config" / "constitution.md"
OUTPUT_PATH = PROJECT_ROOT / "data" / "sft" / "train.jsonl"

MODEL = "gpt-4o-mini"
EXAMPLES_PER_CALL = 8

TOPICS = [
    "variables and assignment",
    "if/elif/else statements",
    "for loops with range()",
    "for loops over lists",
    "while loops",
    "lists — creating and accessing",
    "list methods (append, pop, sort)",
    "IndexError from out-of-range access",
    "tuples and immutability",
    "sets and uniqueness",
    "dictionaries — creating and accessing",
    "KeyError from missing keys",
    "strings and indexing",
    "string methods (split, join, strip, replace)",
    "f-strings and string formatting",
    "functions — defining and calling",
    "function return values (and None)",
    "function arguments — positional and keyword",
    "TypeError from wrong argument count",
    "variable scope (local vs global)",
    "NameError from undefined variables",
    "TypeError from mixing types",
    "using input() and converting to int/float",
    "boolean logic (and, or, not)",
    "comparisons: == vs = confusion",
    "None values and empty returns",
    "mutability — list vs tuple behavior",
    "list comprehensions",
    "enumerate and zip",
    "indentation and IndentationError",
    "off-topic requests (other languages, unrelated questions)",
    "frustrated or rude students",
]

def load_constitution() -> str:
    return CONSTITUTION_PATH.read_text(encoding="utf-8")

def build_generation_prompt(constitution: str, n: int, topic: str) -> str:
    """The instruction we give gpt-4o-mini to produce training examples."""
    return f"""You are helping create training data for a Socratic Python tutor.

Below is the CONSTITUTION defining how the tutor must behave. Every example
you generate must strictly follow it.

<constitution>
{constitution}
</constitution>

FOCUS TOPIC FOR THIS BATCH: {topic}

Every one of the {n} examples in this batch must be about "{topic}".
Vary the scenarios within this topic — different students, different
phrasings, different code snippets — but all centered on "{topic}".

Each example is one exchange:
- A realistic beginner Python question or statement from a student
- A Socratic response from the tutor, obeying the constitution

Mix the styles across the batch (all still about "{topic}"):
- Some concept questions ("what is X?" — where X relates to the topic)
- Some debugging with a code block (student pastes broken code)
- Some frustrated students
- Some students showing partial understanding
- Occasionally a student trying to get a direct answer (tutor redirects)

Vary the Socratic move the tutor uses. Do NOT default to "what did you
expect vs what happened." Other moves:
- Ask about a specific line ("look at line 3 — what's happening there?")
- Ask about a Python concept the bug reveals
- Ask them to mentally run one step
- Ask about the error's location
- Ask about intent
- Ask a metaphor question

Rotate these across examples.

Strict rules:
- The tutor NEVER partially defines or explains. No "X means...",
  "X happens when...", "X occurs when...", "X indicates...". Just ask
  a question or point at code.
- The tutor NEVER meta-comments on its method. Do not say "I can't give
  the answer" — just ask the question.
- Vary how the tutor acknowledges frustration. No canned "I understand
  it can be tough."
- At least 30% of examples should include a code block in Python fences,
  with a realistic beginner bug related to "{topic}".
- The tutor may reference lines or regions but MUST NOT rewrite code or
  state the fix in words.

Output ONLY valid JSON in this exact shape, nothing else:

{{
  "examples": [
    {{"student": "...", "tutor": "..."}},
    ...
  ]
}}
"""

def generate_batch(constitution:str, n:int, topic:str):
    response = client.chat.completions.create(
        model = MODEL,
        messages= [
            {"role":"user", "content":build_generation_prompt(constitution, n, topic)}
        ],
        response_format={"type":"json_object"},
        temperature=0.9
    )
    content = response.choices[0].message.content
    data = json.loads(content)
    return data["examples"]

def to_training_format(example: dict):
    return {
        "messages": [
            {"role": "user", "content": example["student"]},
            {"role": "assistant", "content": example["tutor"]},
        ]
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=len(TOPICS),
                    help="Number of topics to run (default: all).")
    parser.add_argument("--output", type=str, default=str(OUTPUT_PATH),
                        help="Output JSONL path.")
    args = parser.parse_args()

    constitution = load_constitution()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    topics_to_run = TOPICS[: args.n] if args.n < len(TOPICS) else TOPICS
    total_batches = len(topics_to_run)

    print(f"Generating {total_batches} batches of {EXAMPLES_PER_CALL} "
        f"examples each (~{total_batches * EXAMPLES_PER_CALL} total)...")

    written = 0
    with output_path.open("w", encoding="utf-8") as f:
        for i, topic in enumerate(topics_to_run):
            try:
                examples = generate_batch(constitution, EXAMPLES_PER_CALL, topic)
            except Exception as e:
                print(f"  Batch {i+1} ({topic}) failed: {e}. Skipping.")
                continue

            for ex in examples:
                if "student" in ex and "tutor" in ex:
                    f.write(json.dumps(to_training_format(ex)) + "\n")
                    written += 1

            print(f"  Batch {i+1}/{total_batches} [{topic}] done. "
                f"Total written: {written}")

    print(f"\nDone. Wrote {written} examples to {output_path}")


if __name__ == "__main__":
    main()
