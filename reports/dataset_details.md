# CA Disaster Recovery Chatbot — Dataset Report

**Dataset:** 306 question-answer pairs across 34 topics  
**Sources scraped:** 28 of 33 attempted  
**Question styles:** 6  
**Evaluation dimensions:** 6  

---

## 1. Data Sources

The dataset is grounded in 33 authoritative public-facing web pages drawn from federal and California state agencies, legal aid organisations, and disaster-specific programmes. The sources were selected to cover the full topic distribution, from the highest-volume queries (FEMA registration) to specialised long-tail needs (agricultural relief, immigrant rights). Pages were fetched and cleaned using `trafilatura`, capped at 12,000 characters each.

**28 of 33 sources were successfully scraped** (372,065 characters of reference text total). The 5 failures were due to server-side scraper blocks (HTTP 403) or DNS resolution failures, not content unavailability.

### 1.1 Sources by agency

| Agency / Organisation | Pages | Status | Topic coverage |
|---|---:|---|---|
| **FEMA** | 5 | All OK | Registration, individual assistance, housing, appeals, after-applying |
| **California state (CalOES, ca.gov)** | 3 | All OK | Wildfire recovery, general disaster portal, individual & family resources |
| **CA Dept. of Insurance** | 2 | All OK | Catastrophe resources, filing disaster claims |
| **SBA (Small Business Administration)** | 3 | All OK | Disaster loans overview, home loans, economic injury loans |
| **EDD (CA Employment Development Dept.)** | 1 | OK | Disaster Unemployment Assistance |
| **IRS** | 1 | OK | Federal disaster tax relief |
| **CA FTB (Franchise Tax Board)** | 1 | Failed (403) | State disaster tax relief |
| **Red Cross** | 1 | Failed (403) | Disaster relief services |
| **CalRecycle** | 1 | OK | Disaster debris removal |
| **Ready for Wildfire** | 1 | Failed (403) | Post-wildfire recovery steps |
| **CPUC** | 1 | OK | Utility disruptions |
| **CDSS** | 1 | OK | CalFresh / food assistance |
| **SAMHSA** | 1 | OK | Disaster distress helpline |
| **CA DOJ / Attorney General** | 1 | OK | Immigrant know-your-rights |
| **LawHelpCA** | 1 | Failed (conn.) | Disaster legal aid |
| **211 LA / 211.org** | 2 | All OK | Disaster resources, housing help |
| **CSLB** | 1 | OK | Disaster contractor fraud prevention |
| **CA Earthquake Authority** | 1 | OK | Post-earthquake guidance |
| **FloodSmart (FEMA/NFIP)** | 1 | OK | After-flood recovery |
| **CA DMV** | 1 | OK | Driver's licence replacement |
| **HCD (Housing & Community Dev.)** | 1 | OK | Renter protections factsheet |
| **ReCoverCA (HCD)** | 1 | Failed (DNS) | Housing recovery programme |

### 1.2 Content volume by successful source

The single largest source by character count was the HCD renter protections PDF (263,724 chars), followed by the IRS disaster tax relief page (35,737 chars) and the CA DOJ immigrant rights page (20,111 chars). Most other pages returned 400–8,000 characters of extracted body text — appropriate for a focused government resource page.

---

## 2. Topics and Q&A Pair Distribution

The 34 topics are organised into four tiers that reflect real-world query volume — tier 1 topics are the most commonly searched in the immediate aftermath of a disaster; tier 4 topics represent important but less frequent long-tail needs.

The number of Q&A pairs per topic scales with tier: **tier 1 → 16 pairs, tier 2 → 12, tier 3 → 8, tier 4 → 5.**

### Tier 1 — Critical (80 pairs)

These are the first things affected Californians search for after a disaster declaration.

| Topic | Pairs |
|---|---:|
| FEMA registration and individual assistance | 16 |
| Temporary housing and shelters | 16 |
| How to apply for disaster aid (eligibility, deadlines) | 16 |
| Filing insurance claims after a disaster | 16 |
| Disaster unemployment assistance (DUA) | 16 |

### Tier 2 — High Volume (96 pairs)

Needs that arise in the first days and weeks of recovery.

| Topic | Pairs |
|---|---:|
| SBA disaster loans for homeowners and businesses | 12 |
| Food and water assistance (CalFresh, food banks) | 12 |
| Power/utility restoration and outage reporting | 12 |
| Debris and hazardous material removal | 12 |
| Document replacement (ID, birth certificate, DMV) | 12 |
| Tax filing extensions and disaster tax relief | 12 |
| Wildfire-specific recovery steps | 12 |
| Earthquake-specific recovery steps | 12 |

### Tier 3 — Moderate (64 pairs)

Important but less immediately urgent topics, or those requiring more situational context.

| Topic | Pairs |
|---|---:|
| Mental health and emotional support after a disaster | 8 |
| Renter rights and protections after disaster damage | 8 |
| School closures and re-opening | 8 |
| FEMA appeals process | 8 |
| Contractor licensing and avoiding post-disaster fraud | 8 |
| Flood insurance and NFIP claims | 8 |
| Medical needs, prescriptions, and hospital access | 8 |
| Small business recovery | 8 |

### Tier 4 — Long Tail (66 pairs)

Specialised needs affecting subpopulations or arising in later recovery phases.

| Topic | Pairs |
|---|---:|
| Resources for undocumented / mixed-status families | 5 |
| Livestock and large animal evacuation and recovery | 5 |
| Pet-friendly shelters and veterinary assistance | 5 |
| Seniors and people with disabilities — special assistance | 5 |
| Replacing a car or vehicle damaged in disaster | 6 |
| Internet, phone, and communications outages | 5 |
| Workers' comp and job protection during evacuation | 5 |
| Agricultural disaster relief for farmers | 5 |
| Emotional support for children after a disaster | 5 |
| Long-term recovery: rebuilding permits and zoning | 5 |
| Donated goods and volunteer coordination | 5 |
| Water quality testing after flooding | 5 |
| Mold remediation guidance | 5 |

---

## 3. Nature of the Questions

Questions were generated to be **ecologically valid** — reflecting the full range of ways that real Californians in a post-disaster situation would type into a chatbot, not how a professional would phrase a query. Each question is annotated with one of six writing styles.

### 3.1 Style distribution

| Style | Count | Share | Defining characteristics |
|---|---:|---:|---|
| Terse | 80 | 26.1% | 3–16 words, no punctuation, all lowercase, keyword-search register |
| Grammatical | 60 | 19.6% | 8–18 words, proper capitalisation, ends with `?`, question-word opener |
| Personal context | 52 | 17.0% | 6–40 words, embeds situational detail before the question |
| Typo | 41 | 13.4% | Misspellings, missing apostrophes, run-on words |
| Follow-up | 38 | 12.4% | Presupposes a prior exchange ("what if I already filed") |
| Conversational | 35 | 11.4% | 16–46 words, informal opener, narrative structure |

### 3.2 Key linguistic properties by style

| Property | Terse | Gramm. | Personal | Typo | Follow-up | Conv. |
|---|---:|---:|---:|---:|---:|---:|
| Mean word count | 8.5 | 12.2 | 20.9 | 11.5 | 12.9 | **30.8** |
| All-lowercase | **100%** | 7% | 29% | 95% | 92% | 46% |
| Ends with `?` | 0% | **92%** | 73% | 0% | 5% | 74% |
| First-person (I/my/we) | 71% | 62% | **100%** | 71% | 95% | **100%** |
| Informal opener | 9% | 0% | 6% | 2% | 16% | **91%** |
| Opens with question word | 65% | **98%** | 6% | 76% | 55% | 3% |
| Multi-sentence | 0% | 0% | 27% | 0% | 0% | **29%** |

### 3.3 Representative examples

**Terse**
> `can i apply for fema and sba at the same time`

**Grammatical**
> `How do I file a homeowner's insurance claim after a wildfire?`

**Personal context**
> `I'm a renter in LA and my landlord says I have to leave because of the damage, what are my rights?`

**Typo**
> `how long does FEMA aproval take`

**Follow-up**
> `what if i already submitted but never heard back`

**Conversational**
> `hi um i've been having really bad nightmares ever since we evacuated and i can't sleep and i keep thinking the fire is coming back is something wrong with me`

### 3.4 Corpus vocabulary

The full question corpus contains **4,534 tokens** and **853 unique word types** (type-token ratio: 0.188). The most frequent content terms — `fema` (63), `fire` (45), `disaster` (40), `insurance`, `apply`, `housing` — confirm that the vocabulary is tightly domain-grounded. First-person pronouns dominate: `i` (242 occurrences) and `my` (146) are the top two content words, reflecting that users always ask about their own situation, not abstract policy.

The 15 most common opening words are: `how`, `hi`, `can`, `what`, `i`, `my`, `i'm`, `do`, `does`, `is`, `where`, `are`, `will`, `lost`, `im`. The presence of `hi` (33 occurrences) as the second most common opener is a distinct conversational-style signal — users greeting the chatbot before stating their need.

---

## 4. Evaluation Method

Answers are scored using an **LLM-as-judge rubric** (`evaluate_qa.py`). For each question, a judge model (Claude Opus) is shown the question, the gold answer, and the candidate answer, and asked to score the candidate on six dimensions with a 1–5 integer scale plus a one-sentence rationale per dimension.

### 4.1 Rubric dimensions

| Dimension | Weight | Scale anchors |
|---|---:|---|
| **Factual Accuracy** | 30% | 1 = multiple factual errors · 3 = mostly correct, minor slip · 5 = fully accurate |
| **Completeness** | 20% | 1 = misses the main point · 3 = covers main point, misses secondary · 5 = fully covers the question |
| **Actionability** | 20% | 1 = no actionable guidance · 3 = vague guidance · 5 = clear, specific next step(s) |
| **Tone & Empathy** | 10% | 1 = cold/bureaucratic · 3 = neutral · 5 = warm, clear, and efficient |
| **Conciseness** | 10% | 1 = far too long or far too short · 3 = acceptable · 5 = ideal chatbot length |
| **Hallucination (inverse)** | 10% | 1 = clear fabrications · 3 = one uncertain claim · 5 = no hallucinations |

The **weighted score** is Σ(score × weight), producing a single value between 1.0 and 5.0.

Factual accuracy carries the heaviest weight (30%) because incorrect information in a disaster context can cause direct harm — directing someone to the wrong agency or quoting a wrong phone number when they are displaced and stressed is a critical failure. Actionability (20%) is equally prioritised alongside completeness because a factually correct but vague answer fails users who need to know what to do next.

### 4.2 Evaluation outputs

For each evaluated pair the scorer saves:
- Integer score (1–5) and one-sentence rationale for each dimension
- Weighted composite score
- Optional `overall_notes` summary

Aggregate outputs include mean scores broken down by **tier** (critical vs long-tail) and **question style** (terse vs conversational etc.), which surfaces systematic model weaknesses — for example, a model that handles grammatical questions well but degrades on terse or typo-laden queries.

### 4.3 Ceiling benchmark

Running `--self-eval` scores the gold answers against themselves. This functions as a ceiling check: well-formed gold answers should score 4.5–5.0. Significant deviation indicates a data quality issue in the gold set rather than a model failure.

### 4.4 Usage

```bash
# Evaluate a model's predictions
python3 evaluate_qa.py --predictions predictions.jsonl

# Ceiling / sanity check
python3 evaluate_qa.py --self-eval

# Smoke test on 10 pairs
python3 evaluate_qa.py --self-eval --max-pairs 10
```

Predictions file format — one JSON object per line:
```json
{"question": "can i apply for fema and sba at the same time", "answer": "..."}
```

---

## 5. Dataset at a Glance

| Property | Value |
|---|---|
| Total Q&A pairs | 306 |
| Topics | 34 |
| Question styles | 6 |
| Sources attempted | 33 |
| Sources successfully scraped | 28 (85%) |
| Reference text ingested | 372,065 characters |
| Mean question length | 13.5 words |
| First-person question rate | 78% |
| Evaluation dimensions | 6 |
| Max weighted score | 5.0 |
