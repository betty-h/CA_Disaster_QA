"""
evaluate_qa.py

LLM-as-judge rubric evaluator for California disaster recovery chatbot answers.
Scores a set of model predictions against gold answers on six dimensions,
then produces per-pair scores, aggregate statistics, and a Markdown report.

Input files
-----------
  qa_pairs.json        : gold Q&A pairs produced by generate_qa_pairs.py
  predictions.jsonl    : one JSON object per line, each with keys:
                           "question"  (must match a gold pair)
                           "answer"    (the model's output to evaluate)

  Alternatively, pass --self-eval to score the gold answers against themselves
  (useful as a ceiling / sanity check).

Output files
------------
  eval_results.json      : per-pair scores + aggregates (written at end)
  eval_report.md         : human-readable summary (written at end)
  eval_progress.jsonl    : one result per line, written immediately after each
                           pair is scored — used to resume interrupted runs

Usage
-----
  export ANTHROPIC_API_KEY=sk-ant-...
  python evaluate_qa.py --predictions predictions.jsonl
  python evaluate_qa.py --self-eval               # score gold vs gold
  python evaluate_qa.py --predictions preds.jsonl --output-prefix run1
"""

import argparse
import json
import logging
import os
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional

import anthropic

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Rubric definition ─────────────────────────────────────────────────────────

DIMENSIONS = [
    {
        "key": "factual_accuracy",
        "name": "Factual Accuracy",
        "weight": 0.30,
        "description": (
            "Are the facts, program names, eligibility rules, phone numbers, and URLs "
            "in the evaluated answer correct relative to the gold answer and general "
            "knowledge of CA/federal disaster recovery programs? "
            "Penalise wrong agency names, wrong phone numbers, wrong eligibility rules."
        ),
        "scale": "1 = multiple factual errors  |  3 = mostly correct, minor slip  |  5 = fully accurate",
    },
    {
        "key": "completeness",
        "name": "Completeness",
        "weight": 0.20,
        "description": (
            "Does the evaluated answer cover the core informational needs expressed in "
            "the question and present in the gold answer? A complete answer need not be "
            "exhaustive — it must not omit the most critical point(s)."
        ),
        "scale": "1 = misses the main point  |  3 = covers main point, misses secondary  |  5 = fully covers the question",
    },
    {
        "key": "actionability",
        "name": "Actionability",
        "weight": 0.20,
        "description": (
            "Does the answer give the user at least one clear, concrete next step "
            "(e.g., a URL to visit, a number to call, a form to file)? "
            "Disaster victims need to know what to DO, not just what exists."
        ),
        "scale": "1 = no actionable guidance  |  3 = vague guidance  |  5 = clear, specific next step(s)",
    },
    {
        "key": "tone",
        "name": "Tone & Empathy",
        "weight": 0.10,
        "description": (
            "Is the tone appropriate for a stressed, possibly grieving disaster victim? "
            "It should be warm but efficient — not cold/bureaucratic, not excessively "
            "verbose, and not dismissive. Penalise clinical jargon without explanation "
            "and unnecessary caveats that delay the useful information."
        ),
        "scale": "1 = cold/dismissive/jargon-heavy  |  3 = neutral  |  5 = warm, clear, and efficient",
    },
    {
        "key": "conciseness",
        "name": "Conciseness",
        "weight": 0.10,
        "description": (
            "Is the response an appropriate length for a chatbot reply? "
            "Target: 2–6 sentences. Penalise unnecessary padding, repeated information, "
            "or walls of text. Also penalise answers so short they omit essential info "
            "(that would be captured by the Completeness dimension too)."
        ),
        "scale": "1 = far too long or far too short  |  3 = acceptable  |  5 = ideal chatbot length",
    },
    {
        "key": "hallucination",
        "name": "Hallucination (inverse)",
        "weight": 0.10,
        "description": (
            "Does the answer introduce specific claims that are NOT in the gold answer "
            "AND are not verifiable general knowledge — e.g., invented dollar amounts, "
            "fabricated program names, made-up deadlines? "
            "NOTE: this dimension is scored inversely — 5 means NO hallucinations."
        ),
        "scale": "1 = clear fabrications  |  3 = one uncertain/unverifiable claim  |  5 = no hallucinations",
    },
]

TOTAL_WEIGHT = sum(d["weight"] for d in DIMENSIONS)  # should be 1.0

# ── Judge prompt ──────────────────────────────────────────────────────────────

JUDGE_SYSTEM = """\
You are an expert evaluator for a California disaster recovery chatbot dataset.
Your job is to score a candidate answer against a gold-standard answer using a \
provided rubric. You must be rigorous and consistent.
Always return valid JSON and nothing else.
"""

JUDGE_USER_TEMPLATE = """\
## Question
{question}

## Gold Answer (reference)
{gold_answer}

## Candidate Answer (to evaluate)
{candidate_answer}

## Rubric
{rubric_block}

## Instructions
Score the candidate answer on each dimension (integer 1–5).
For each dimension also write a 1-sentence rationale.
Return ONLY a JSON object with this exact structure:
{{
  "scores": {{
    "<dimension_key>": {{
      "score": <int 1-5>,
      "rationale": "<one sentence>"
    }},
    ...
  }},
  "overall_notes": "<optional 1-2 sentence summary of the main strengths/weaknesses>"
}}
"""

def build_rubric_block() -> str:
    lines = []
    for d in DIMENSIONS:
        lines.append(
            f"### {d['name']} (key: `{d['key']}`, weight: {d['weight']:.0%})\n"
            f"{d['description']}\n"
            f"Scale: {d['scale']}"
        )
    return "\n\n".join(lines)

RUBRIC_BLOCK = build_rubric_block()


# ── Evaluation ────────────────────────────────────────────────────────────────

def compute_weighted_score(scores: dict) -> float:
    total = 0.0
    for d in DIMENSIONS:
        raw = scores.get(d["key"], {}).get("score", 0)
        total += raw * d["weight"]
    return round(total, 3)


def evaluate_pair(
    client: anthropic.Anthropic,
    question: str,
    gold_answer: str,
    candidate_answer: str,
    model: str,
    max_retries: int = 3,
) -> Optional[dict]:
    prompt = JUDGE_USER_TEMPLATE.format(
        question=question,
        gold_answer=gold_answer,
        candidate_answer=candidate_answer,
        rubric_block=RUBRIC_BLOCK,
    )
    for attempt in range(1, max_retries + 1):
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=1024,
                system=JUDGE_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text.strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            result = json.loads(raw)
            # Validate
            if "scores" not in result:
                raise ValueError("Missing 'scores' key")
            for d in DIMENSIONS:
                if d["key"] not in result["scores"]:
                    raise ValueError(f"Missing dimension: {d['key']}")
                s = result["scores"][d["key"]].get("score")
                if not isinstance(s, int) or not (1 <= s <= 5):
                    raise ValueError(f"Invalid score for {d['key']}: {s}")
            result["weighted_score"] = compute_weighted_score(result["scores"])
            return result
        except (json.JSONDecodeError, ValueError, anthropic.APIError) as exc:
            log.warning(f"  Attempt {attempt} failed: {exc}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)
    return None


# ── Data loading ──────────────────────────────────────────────────────────────

def load_gold(path: str) -> dict[str, dict]:
    """Returns {question_text: gold_pair_dict}."""
    with open(path, encoding="utf-8") as f:
        pairs = json.load(f)
    return {p["question"]: p for p in pairs}


def load_predictions(path: str) -> list[dict]:
    preds = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                preds.append(json.loads(line))
    return preds


# ── Aggregation ───────────────────────────────────────────────────────────────

def aggregate(results: list[dict]) -> dict:
    def mean(vals):
        return round(sum(vals) / len(vals), 3) if vals else 0.0

    def bucket_stats(key_fn):
        grouped = defaultdict(list)
        for r in results:
            grouped[key_fn(r)].append(r["weighted_score"])
        return {k: {"n": len(v), "mean_weighted": mean(v)} for k, v in sorted(grouped.items())}

    dim_means = {}
    for d in DIMENSIONS:
        scores = [r["eval"]["scores"][d["key"]]["score"] for r in results if r.get("eval")]
        dim_means[d["key"]] = mean(scores)

    score_dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    for r in results:
        ws = r.get("weighted_score", 0)
        bucket = str(min(5, max(1, round(ws))))
        score_dist[bucket] += 1

    return {
        "n_evaluated": len(results),
        "n_failed": sum(1 for r in results if not r.get("eval")),
        "mean_weighted_score": mean([r["weighted_score"] for r in results if "weighted_score" in r]),
        "dimension_means": dim_means,
        "by_tier": bucket_stats(lambda r: r.get("tier", "unknown")),
        "by_style": bucket_stats(lambda r: r.get("style", "unknown")),
        "score_distribution": score_dist,
    }


# ── Markdown report ───────────────────────────────────────────────────────────

def build_report(results: list[dict], agg: dict, pred_source: str) -> str:
    lines = [
        "# CA Disaster Recovery Chatbot — Evaluation Report",
        "",
        f"**Predictions file:** `{pred_source}`  ",
        f"**Pairs evaluated:** {agg['n_evaluated']}  ",
        f"**Evaluation failures:** {agg['n_failed']}  ",
        "",
        "---",
        "",
        "## Overall Score",
        "",
        f"**Mean weighted score: {agg['mean_weighted_score']:.3f} / 5.000**",
        "",
        "### Rubric weights",
        "",
        "| Dimension | Weight | Mean Score |",
        "|-----------|-------:|----------:|",
    ]
    for d in DIMENSIONS:
        mean_s = agg["dimension_means"].get(d["key"], 0)
        lines.append(f"| {d['name']} | {d['weight']:.0%} | {mean_s:.2f} |")

    lines += [
        "",
        "---",
        "",
        "## Scores by Tier",
        "",
        "| Tier | N | Mean Weighted Score |",
        "|------|--:|--------------------:|",
    ]
    for tier, stats in agg["by_tier"].items():
        lines.append(f"| {tier} | {stats['n']} | {stats['mean_weighted']:.3f} |")

    lines += [
        "",
        "## Scores by Question Style",
        "",
        "| Style | N | Mean Weighted Score |",
        "|-------|--:|--------------------:|",
    ]
    for style, stats in agg["by_style"].items():
        lines.append(f"| {style} | {stats['n']} | {stats['mean_weighted']:.3f} |")

    lines += [
        "",
        "---",
        "",
        "## Lowest-Scoring Pairs (bottom 10)",
        "",
    ]
    sorted_results = sorted(
        [r for r in results if "weighted_score" in r],
        key=lambda r: r["weighted_score"],
    )
    for r in sorted_results[:10]:
        lines += [
            f"**Score: {r['weighted_score']:.3f}** | Topic: {r.get('topic', '?')} | Style: {r.get('style', '?')}",
            f"> **Q:** {r['question'][:120]}",
            f"> **Gold:** {r['gold_answer'][:120]}",
            f"> **Predicted:** {r['candidate_answer'][:120]}",
            f"> *{r['eval'].get('overall_notes', '')}*" if r.get("eval") else "",
            "",
        ]

    lines += [
        "---",
        "",
        "## Dimension Definitions",
        "",
    ]
    for d in DIMENSIONS:
        lines += [
            f"### {d['name']}",
            d["description"],
            f"*Scale:* {d['scale']}",
            "",
        ]

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Evaluate CA disaster recovery chatbot answers")
    parser.add_argument("--gold",           default="qa_pairs.json",          help="Gold Q&A pairs JSON")
    parser.add_argument("--predictions",    default=None,                      help="Predictions JSONL (question + answer)")
    parser.add_argument("--self-eval",      action="store_true",               help="Score gold answers against themselves (ceiling check)")
    parser.add_argument("--output-prefix",  default="eval",                    help="Prefix for output files")
    parser.add_argument("--model",          default="claude-opus-4-7",         help="Judge model")
    parser.add_argument("--delay",          type=float, default=0.5,           help="Seconds between API calls")
    parser.add_argument("--max-pairs",      type=int,   default=None,          help="Evaluate only the first N pairs (useful for testing)")
    args = parser.parse_args()

    if not args.predictions and not args.self_eval:
        parser.error("Provide --predictions <file> or --self-eval")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: ANTHROPIC_API_KEY environment variable not set.")

    client = anthropic.Anthropic(api_key=api_key)

    log.info(f"Loading gold pairs from {args.gold} …")
    gold_map = load_gold(args.gold)
    log.info(f"  {len(gold_map)} gold pairs loaded")

    if args.self_eval:
        predictions = [{"question": p["question"], "answer": p["answer"]} for p in gold_map.values()]
        pred_source = "(self-eval: gold vs gold)"
    else:
        log.info(f"Loading predictions from {args.predictions} …")
        predictions = load_predictions(args.predictions)
        pred_source = args.predictions

    if args.max_pairs:
        predictions = predictions[: args.max_pairs]

    # ── Resume support: load already-scored questions from progress file ──────
    progress_path = Path(f"{args.output_prefix}_progress.jsonl")
    results: list[dict] = []
    already_done: set[str] = set()

    if progress_path.exists():
        with open(progress_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    record = json.loads(line)
                    results.append(record)
                    already_done.add(record["question"])
        log.info(f"Resuming — loaded {len(already_done)} already-scored pairs from {progress_path}")

    remaining = [p for p in predictions if p.get("question", "").strip() not in already_done]
    log.info(f"Evaluating {len(remaining)} remaining pairs (of {len(predictions)} total) with model: {args.model}")

    failed_lookup = 0

    with open(progress_path, "a", encoding="utf-8") as progress_file:
        for i, pred in enumerate(remaining, 1):
            q = pred.get("question", "").strip()
            candidate = pred.get("answer", "").strip()

            gold_pair = gold_map.get(q)
            if gold_pair is None:
                # Fuzzy fallback: try prefix match (handles minor whitespace diffs)
                for gq, gp in gold_map.items():
                    if gq.strip().lower() == q.lower():
                        gold_pair = gp
                        break

            if gold_pair is None:
                log.warning(f"[{i}] No gold match for question: {q[:60]}…")
                failed_lookup += 1
                continue

            gold_answer = gold_pair["answer"]
            log.info(f"[{i}/{len(remaining)}] Evaluating: {q[:60]}…")

            eval_result = evaluate_pair(
                client=client,
                question=q,
                gold_answer=gold_answer,
                candidate_answer=candidate,
                model=args.model,
            )

            record = {
                "question":         q,
                "gold_answer":      gold_answer,
                "candidate_answer": candidate,
                "topic":            gold_pair.get("topic", ""),
                "tier":             gold_pair.get("tier", ""),
                "style":            gold_pair.get("style", ""),
                "eval":             eval_result,
                "weighted_score":   eval_result["weighted_score"] if eval_result else None,
            }
            results.append(record)

            # Write immediately so progress survives interruption
            progress_file.write(json.dumps(record, ensure_ascii=False) + "\n")
            progress_file.flush()

            if i < len(remaining):
                time.sleep(args.delay)

    if failed_lookup:
        log.warning(f"{failed_lookup} predictions had no matching gold question (skipped).")

    evaluated = [r for r in results if r["eval"] is not None]
    log.info(f"Evaluated: {len(evaluated)} / {len(results)}")

    agg = aggregate(evaluated)

    # ── Save results JSON ──────────────────────────────────────────────────
    results_path = f"{args.output_prefix}_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({"aggregates": agg, "pairs": results}, f, indent=2, ensure_ascii=False)
    log.info(f"Saved → {results_path}")

    # ── Save Markdown report ───────────────────────────────────────────────
    report_path = f"{args.output_prefix}_report.md"
    report = build_report(evaluated, agg, pred_source)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    log.info(f"Saved → {report_path}")

    # ── Print summary ──────────────────────────────────────────────────────
    print("\n── Evaluation Summary ─────────────────────────────────────────")
    print(f"Pairs evaluated :  {agg['n_evaluated']}")
    print(f"Mean weighted   :  {agg['mean_weighted_score']:.3f} / 5.000")
    print("\nDimension means:")
    for d in DIMENSIONS:
        mean_s = agg["dimension_means"].get(d["key"], 0)
        bar = "█" * round(mean_s) + "░" * (5 - round(mean_s))
        print(f"  {d['name']:<28} {bar}  {mean_s:.2f}")
    print("───────────────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
