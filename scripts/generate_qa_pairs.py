"""
generate_qa_pairs.py

Generates ecologically valid Q&A pairs for a California disaster recovery chatbot.
Reads scraped_content.json (from scrape_disaster_info.py) and uses the Claude API
to produce questions that reflect how real people type — from urgent and terse to
detailed and confused — across the full topic distribution.

Outputs:
  - qa_pairs.json   : structured list of QA objects
  - qa_pairs.jsonl  : one JSON object per line (convenient for fine-tuning)

Usage:
  export ANTHROPIC_API_KEY=sk-ant-...
  python generate_qa_pairs.py [--pairs-per-topic 8] [--output qa_pairs.json]
"""

import argparse
import json
import logging
import os
import random
import re
import time
from pathlib import Path
from typing import Optional

import anthropic

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Prompt templates ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a researcher creating a benchmark dataset of question-answer pairs for a \
California disaster recovery chatbot. Your job is to produce Q&A pairs that are \
ecologically valid — they must reflect the full range of ways that real people \
(Californians in a stressful post-disaster situation) would type queries into a \
chatbot, NOT how a professional would phrase questions.

Ecological validity rules:
1. MIX query styles proportionally:
   - ~25% terse / urgent (3–8 words, no punctuation): "where do i register for fema"
   - ~20% conversational / run-on: "hi i lost my house in the fires and i don't know \
what to do first, can i get help with temporary housing?"
   - ~20% grammatically normal questions: "How do I file an insurance claim after a \
wildfire?"
   - ~15% with typos or autocorrect artifacts: "how long does FEMA aproval take"
   - ~10% containing personal context: "I'm a renter in LA and my landlord says I have \
to leave, what are my rights?"
   - ~10% follow-up / clarifying style: "what if i already filed but never heard back"

2. Vary demographics and tone — anxious first-timers, older residents unfamiliar \
with technology, Spanish speakers writing in English, small business owners, \
undocumented families, farmers, pet owners.

3. Answers must be accurate, helpful, and actionable. Cite programs by name \
(FEMA, DUA, SBA, 211, etc.). Include phone numbers or URLs only if they are \
well-known and stable (e.g., 1-800-621-3362 for FEMA).

4. Answers should be concise chatbot responses (2–6 sentences), not essays.

5. Each QA pair must have a "topic" tag from the taxonomy provided.
"""

USER_PROMPT_TEMPLATE = """\
Below is reference content scraped from official California and federal disaster \
recovery websites. Use it to write {n} ecologically valid question-answer pairs \
about the topic: **{topic}**.

---REFERENCE CONTENT---
{context}
---END REFERENCE CONTENT---

Return ONLY a JSON array of objects. Each object must have exactly these fields:
  "question"   : the user query (ecologically realistic)
  "answer"     : the chatbot response (accurate, concise, actionable)
  "topic"      : "{topic}"
  "tier"       : "{tier}"
  "style"      : one of ["terse","conversational","grammatical","typo","personal_context","follow_up"]

Output no prose, no markdown fences, just the raw JSON array.
"""

# ── Topic → tier mapping (mirrors scrape_disaster_info.py) ──────────────────

TOPIC_TIERS = {}  # populated from scraped_content.json

# ── Utility ──────────────────────────────────────────────────────────────────

def load_scraped(path: str = "scraped_content.json") -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_context_for_topic(topic: str, pages: list[dict], max_chars: int = 6_000) -> str:
    """
    Find pages whose category or label is relevant to the topic,
    concatenate their text up to max_chars.
    """
    topic_lower = topic.lower()
    keywords = set(re.findall(r"\b\w{4,}\b", topic_lower))

    def relevance(page: dict) -> int:
        score = 0
        combined = (page["category"] + " " + page["label"] + " " + page["text"][:500]).lower()
        for kw in keywords:
            score += combined.count(kw)
        return score

    ranked = sorted(
        [p for p in pages if p.get("text")],
        key=relevance,
        reverse=True,
    )

    chunks = []
    total = 0
    for page in ranked[:6]:  # at most 6 pages per topic
        snippet = page["text"][: max_chars - total]
        if snippet.strip():
            chunks.append(f"### {page['label']} ({page['url']})\n{snippet}")
            total += len(snippet)
        if total >= max_chars:
            break

    return "\n\n".join(chunks) if chunks else "(No specific reference found; use general CA disaster recovery knowledge.)"


def generate_qa_batch(
    client: anthropic.Anthropic,
    topic: str,
    tier: str,
    context: str,
    n: int,
    model: str = "claude-opus-4-7",
    max_retries: int = 3,
) -> list[dict]:
    prompt = USER_PROMPT_TEMPLATE.format(
        n=n,
        topic=topic,
        tier=tier,
        context=context,
    )

    for attempt in range(1, max_retries + 1):
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text.strip()

            # Strip markdown fences if the model adds them despite instructions
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            pairs = json.loads(raw)
            if not isinstance(pairs, list):
                raise ValueError("Expected a JSON array")

            # Validate fields
            valid = []
            for p in pairs:
                if all(k in p for k in ("question", "answer", "topic", "tier", "style")):
                    valid.append(p)
                else:
                    log.warning(f"  Skipping malformed pair: {list(p.keys())}")
            return valid

        except (json.JSONDecodeError, ValueError, anthropic.APIError) as exc:
            log.warning(f"  Attempt {attempt} failed: {exc}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)

    log.error(f"  All {max_retries} attempts failed for topic: {topic}")
    return []


# ── Pairs-per-topic allocation ───────────────────────────────────────────────

def compute_allocations(topic_distribution: dict, base_per_topic: int) -> dict[str, int]:
    """
    Tier 1 topics get 2× base, tier 2 get 1.5×, tier 3 get 1×, tier 4 get 0.6×.
    Returns {topic: n_pairs}.
    """
    multipliers = {
        "tier_1_critical": 2.0,
        "tier_2_high_volume": 1.5,
        "tier_3_moderate": 1.0,
        "tier_4_long_tail": 0.6,
    }
    allocations = {}
    for tier, topics in topic_distribution.items():
        mult = multipliers.get(tier, 1.0)
        n = max(3, round(base_per_topic * mult))
        for topic in topics:
            allocations[topic] = (n, tier)
    return allocations


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate CA disaster recovery Q&A pairs")
    parser.add_argument("--input",            default="scraped_content.json",  help="Scraped content JSON")
    parser.add_argument("--output",           default="qa_pairs.json",          help="Output JSON path")
    parser.add_argument("--pairs-per-topic",  type=int, default=8,              help="Base # pairs per topic (tier 1 gets 2×)")
    parser.add_argument("--model",            default="claude-opus-4-7",        help="Claude model to use")
    parser.add_argument("--delay",            type=float, default=1.0,          help="Seconds between API calls")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: ANTHROPIC_API_KEY environment variable not set.")

    client = anthropic.Anthropic(api_key=api_key)

    log.info(f"Loading scraped content from {args.input} …")
    data = load_scraped(args.input)
    pages = data["pages"]
    topic_distribution = data["topic_distribution"]

    allocations = compute_allocations(topic_distribution, args.pairs_per_topic)
    total_topics = len(allocations)
    total_expected = sum(n for n, _ in allocations.values())
    log.info(f"{total_topics} topics  |  ~{total_expected} pairs expected  |  model: {args.model}")

    all_pairs: list[dict] = []

    for i, (topic, (n_pairs, tier)) in enumerate(allocations.items(), 1):
        log.info(f"[{i}/{total_topics}] {tier}  ->  '{topic}'  ({n_pairs} pairs)")
        context = build_context_for_topic(topic, pages)
        pairs = generate_qa_batch(
            client=client,
            topic=topic,
            tier=tier,
            context=context,
            n=n_pairs,
            model=args.model,
        )
        log.info(f"  Generated {len(pairs)} pairs")
        all_pairs.extend(pairs)

        if i < total_topics:
            time.sleep(args.delay)

    # Shuffle so tiers are interleaved in the output
    random.shuffle(all_pairs)

    # ── Save JSON ──────────────────────────────────────────────────────────
    out_path = Path(args.output)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_pairs, f, indent=2, ensure_ascii=False)
    log.info(f"Saved {len(all_pairs)} pairs → {out_path}")

    # ── Save JSONL ─────────────────────────────────────────────────────────
    jsonl_path = out_path.with_suffix(".jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for pair in all_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
    log.info(f"Saved JSONL → {jsonl_path}")

    # ── Summary stats ──────────────────────────────────────────────────────
    from collections import Counter
    tier_counts = Counter(p["tier"] for p in all_pairs)
    style_counts = Counter(p["style"] for p in all_pairs)
    print("\n── Summary ──────────────────────────────────────────")
    print(f"Total pairs: {len(all_pairs)}")
    print("\nBy tier:")
    for tier, count in sorted(tier_counts.items()):
        print(f"  {tier:<30} {count}")
    print("\nBy question style:")
    for style, count in sorted(style_counts.items(), key=lambda x: -x[1]):
        print(f"  {style:<25} {count}")
    print("─────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
