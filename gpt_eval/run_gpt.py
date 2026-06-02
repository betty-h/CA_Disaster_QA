"""
run_gpt.py

Runs a GPT model on every question in qa_pairs.json and saves the answers
to predictions.jsonl, ready for evaluation with evaluate_qa.py.

Usage:
    python run_gpt.py                          # defaults to gpt-4o
    python run_gpt.py --model gpt-4o-mini      # cheaper / faster
    python run_gpt.py --max-questions 20       # smoke test on 20 questions
"""

import argparse
import json
import logging
import os
import time
from pathlib import Path

from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a helpful California disaster recovery assistant.
Answer the user's question concisely and accurately in 2-6 sentences.
Focus on actionable guidance — give specific programme names, phone numbers,
or URLs where relevant. Be warm but efficient.
"""

def run(model: str, input_path: str, output_path: str, max_questions: int | None, delay: float):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: OPENAI_API_KEY environment variable not set.")

    client = OpenAI(api_key=api_key)

    with open(input_path, encoding="utf-8") as f:
        pairs = json.load(f)

    if max_questions:
        pairs = pairs[:max_questions]

    log.info(f"Running {len(pairs)} questions through {model} ...")

    out = Path(output_path)
    with open(out, "w", encoding="utf-8") as f:
        for i, pair in enumerate(pairs, 1):
            question = pair["question"]
            log.info(f"[{i}/{len(pairs)}] {question[:70]}")

            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": question},
                    ],
                    max_tokens=300,
                    temperature=0.3,
                )
                answer = response.choices[0].message.content.strip()
            except Exception as exc:
                log.warning(f"  API error: {exc} — skipping")
                answer = ""

            f.write(json.dumps({"question": question, "answer": answer}, ensure_ascii=False) + "\n")

            if i < len(pairs):
                time.sleep(delay)

    log.info(f"Saved predictions -> {out}")


def main():
    parser = argparse.ArgumentParser(description="Run GPT on the QA dataset")
    parser.add_argument("--model",          default="gpt-4o",          help="OpenAI model name")
    parser.add_argument("--input",          default="qa_pairs.json",   help="Gold QA pairs")
    parser.add_argument("--output",         default="predictions.jsonl",help="Output predictions file")
    parser.add_argument("--max-questions",  type=int, default=None,    help="Limit to first N questions")
    parser.add_argument("--delay",          type=float, default=0.5,   help="Seconds between API calls")
    args = parser.parse_args()

    run(args.model, args.input, args.output, args.max_questions, args.delay)


if __name__ == "__main__":
    main()
