# CA Disaster Recovery Chatbot — Q&A Dataset Pipeline

A three-stage pipeline for building and evaluating a benchmark dataset of question-answer pairs for a California disaster recovery chatbot. Questions are ecologically valid — they reflect how real people type under stress — and cover the full topic distribution from high-volume queries down to long-tail edge cases.

---

## Pipeline Overview

```
scrape_disaster_info.py  →  scraped_content.json
                                     ↓
                         generate_qa_pairs.py  →  qa_pairs.json / qa_pairs.jsonl
                                                            ↓
                                              evaluate_qa.py  →  eval_results.json
                                                                  eval_report.md
```

---

## Setup

**Requirements:** Python 3.9+

```bash
pip install requests beautifulsoup4 trafilatura anthropic lxml
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Stage 1 — Scrape (`scrape_disaster_info.py`)

Fetches and extracts clean text from ~35 authoritative public sources covering the full topic space of CA disaster recovery.

```bash
python3 scrape_disaster_info.py
```

**Output:** `scraped_content.json`

Sources include:

| Category | Sources |
|---|---|
| Federal aid | FEMA individual assistance, SBA disaster loans, IRS tax relief |
| CA state | CalOES, disaster.ca.gov, recovery.ca.gov, EDD disaster unemployment, FTB tax relief |
| Insurance | CA Dept. of Insurance, CA Earthquake Authority |
| Housing | HCD renter protections, 211 housing |
| Food & utilities | CDSS / CalFresh, CPUC outage resources |
| Disaster types | CAL FIRE, CalRecycle debris, FloodSmart, Ready for Wildfire |
| Special populations | CA DOJ immigrant rights, LawHelpCA |
| Documents | DMV, CDPH vital records |
| Fraud prevention | CSLB disaster contractor fraud |
| Mental health | SAMHSA disaster distress helpline, CA DHCS |

The scraper uses `trafilatura` for clean main-body extraction and falls back to BeautifulSoup. Pages are capped at 12,000 characters each. A ~1.5 second delay between requests keeps the scraper polite.

---

## Stage 2 — Generate Q&A Pairs (`generate_qa_pairs.py`)

Uses the Claude API (LLM generation) to produce ecologically valid Q&A pairs grounded in the scraped content.

```bash
python3 generate_qa_pairs.py
```

**Output:** `qa_pairs.json`, `qa_pairs.jsonl`

### Options

| Flag | Default | Description |
|---|---|---|
| `--pairs-per-topic` | `8` | Base number of pairs per topic (see tier multipliers below) |
| `--model` | `claude-opus-4-7` | Claude model to use |
| `--input` | `scraped_content.json` | Scraped content file |
| `--output` | `qa_pairs.json` | Output path |
| `--delay` | `1.0` | Seconds between API calls |

### Topic distribution

Topics are grouped into four tiers that mirror real-world query volume. The `--pairs-per-topic` base is scaled per tier:

| Tier | Multiplier | Example topics |
|---|---|---|
| Tier 1 — Critical | 2× | FEMA registration, temporary housing, insurance claims |
| Tier 2 — High volume | 1.5× | SBA loans, food assistance, debris removal, document replacement |
| Tier 3 — Moderate | 1× | Mental health, renter rights, FEMA appeals, contractor fraud |
| Tier 4 — Long tail | 0.6× | Undocumented families, livestock, pets, agricultural relief |

With the default `--pairs-per-topic 8`, this yields approximately **260 pairs** across 28 topics.

### Ecological validity

Each generation call instructs the model to produce a realistic mix of query styles:

| Style | Target share | Example |
|---|---|---|
| `terse` | ~25% | `where do i register for fema` |
| `conversational` | ~20% | `hi i lost my house in the fires and i don't know what to do first` |
| `grammatical` | ~20% | `How do I file an insurance claim after a wildfire?` |
| `typo` | ~15% | `how long does FEMA aproval take` |
| `personal_context` | ~10% | `I'm a renter in LA and my landlord says I have to leave` |
| `follow_up` | ~10% | `what if i already filed but never heard back` |

The model is also prompted to vary demographics: anxious first-timers, seniors, Spanish speakers writing in English, small business owners, undocumented families, farmers, and pet owners.

### Output schema

Each object in `qa_pairs.json`:

```json
{
  "question": "where do i sign up for disaster help",
  "answer": "You can register for FEMA disaster assistance at DisasterAssistance.gov or by calling 1-800-621-3362. Have your address, insurance info, and a description of damages ready. Apply as soon as possible — there are deadlines.",
  "topic": "FEMA registration and individual assistance",
  "tier": "tier_1_critical",
  "style": "terse"
}
```

---

## Stage 3 — Evaluate (`evaluate_qa.py`)

LLM-as-judge evaluation that scores model-generated answers against the gold answers on six dimensions.

```bash
python3 evaluate_qa.py --predictions predictions.jsonl
```

**Output:** `eval_results.json`, `eval_report.md`

### Input format

`predictions.jsonl` — one JSON object per line:

```jsonl
{"question": "where do i sign up for disaster help", "answer": "Go to DisasterAssistance.gov or call 1-800-621-3362 to apply for FEMA aid."}
{"question": "how long does FEMA aproval take", "answer": "..."}
```

The `question` field must match a question in `qa_pairs.json` exactly (case-insensitive).

### Options

| Flag | Default | Description |
|---|---|---|
| `--gold` | `qa_pairs.json` | Gold Q&A pairs |
| `--predictions` | — | Predictions JSONL to evaluate |
| `--self-eval` | — | Score gold answers against themselves (ceiling check) |
| `--output-prefix` | `eval` | Prefix for output files |
| `--model` | `claude-opus-4-7` | Judge model |
| `--max-pairs` | all | Evaluate only the first N pairs (useful for smoke tests) |

### Rubric

Scores are integers 1–5. The weighted score is Σ(score × weight), max 5.0.

| Dimension | Weight | What is penalised |
|---|---|---|
| **Factual Accuracy** | 30% | Wrong program names, phone numbers, eligibility rules |
| **Completeness** | 20% | Missing the core informational need of the question |
| **Actionability** | 20% | No concrete next step (URL, number, form to file) |
| **Tone & Empathy** | 10% | Cold/bureaucratic language, unexplained jargon |
| **Conciseness** | 10% | Walls of text or uselessly short replies |
| **Hallucination (inverse)** | 10% | Invented dollar amounts, fabricated programs, made-up deadlines |

Each dimension also produces a one-sentence rationale. The judge outputs an `overall_notes` summary per pair.

### Ceiling / sanity check

Run `--self-eval` to score the gold answers against themselves. Expect a mean weighted score of ~4.5–5.0. Significant deviation indicates a prompt or data quality issue.

```bash
python3 evaluate_qa.py --self-eval --max-pairs 10
```

### Output schema

`eval_results.json`:

```json
{
  "aggregates": {
    "n_evaluated": 260,
    "mean_weighted_score": 4.12,
    "dimension_means": { "factual_accuracy": 4.3, "completeness": 4.1, ... },
    "by_tier": { "tier_1_critical": { "n": 80, "mean_weighted": 4.4 }, ... },
    "by_style": { "terse": { "n": 65, "mean_weighted": 3.9 }, ... }
  },
  "pairs": [
    {
      "question": "...",
      "gold_answer": "...",
      "candidate_answer": "...",
      "topic": "...",
      "tier": "...",
      "style": "...",
      "weighted_score": 4.2,
      "eval": {
        "scores": {
          "factual_accuracy": { "score": 5, "rationale": "All program names and numbers are correct." },
          ...
        },
        "overall_notes": "Strong answer — clear and actionable. Slightly long."
      }
    }
  ]
}
```

`eval_report.md` contains a human-readable summary including overall scores, breakdowns by tier and question style, and a bottom-10 table for debugging.

---

## Full Run (end to end)

```bash
# 1. Scrape sources (~2 min, one-time)
python3 scrape_disaster_info.py

# 2. Generate Q&A pairs (~5–10 min depending on pair count)
python3 generate_qa_pairs.py --pairs-per-topic 8

# 3a. Evaluate your model's predictions
python3 evaluate_qa.py --predictions predictions.jsonl

# 3b. Or run the ceiling check on gold answers
python3 evaluate_qa.py --self-eval
```

---

## File Reference

| File | Created by | Description |
|---|---|---|
| `scrape_disaster_info.py` | — | Scraper script |
| `generate_qa_pairs.py` | — | Q&A generation script |
| `evaluate_qa.py` | — | Rubric evaluation script |
| `scraped_content.json` | scraper | Raw text from ~35 sources + topic taxonomy |
| `qa_pairs.json` | generator | Gold Q&A pairs (array) |
| `qa_pairs.jsonl` | generator | Gold Q&A pairs (one per line, for fine-tuning) |
| `eval_results.json` | evaluator | Per-pair scores + aggregates |
| `eval_report.md` | evaluator | Human-readable evaluation summary |
