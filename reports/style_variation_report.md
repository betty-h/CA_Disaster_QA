# Writing Style Variation Report
## CA Disaster Recovery Chatbot — Q&A Dataset (306 questions)

---

## 1. Overview

The dataset contains 306 questions distributed across six annotated writing styles. The analysis below measures whether questions in each style are linguistically distinct on dimensions that matter for a chatbot benchmark: length, formality, punctuation, person, and vocabulary.

| Style | Count | Share |
|---|---:|---:|
| Terse | 80 | 26.1% |
| Grammatical | 60 | 19.6% |
| Personal context | 52 | 17.0% |
| Typo | 41 | 13.4% |
| Follow-up | 38 | 12.4% |
| Conversational | 35 | 11.4% |
| **Total** | **306** | **100%** |

---

## 2. Length Distribution

### 2.1 By question length bucket (all styles)

| Word count range | Count | Share |
|---|---:|---:|
| 1–5 words | 11 | 3.6% |
| 6–10 words | 98 | 32.0% |
| 11–20 words | 135 | 44.1% |
| 21–35 words | 51 | 16.7% |
| 36+ words | 11 | 3.6% |

The modal question is 11–20 words. Very short (≤5) and very long (36+) questions each account for under 4%, which is consistent with real chatbot query distributions.

### 2.2 Mean word count by style

| Style | Mean | Median | Stdev | Min | Max |
|---|---:|---:|---:|---:|---:|
| Conversational | 30.8 | 30 | 6.6 | 16 | 46 |
| Personal context | 20.9 | 20.5 | 7.0 | 6 | 40 |
| Grammatical | 12.2 | 12.0 | 2.6 | 8 | 18 |
| Typo | 11.5 | 12.0 | 3.0 | 4 | 17 |
| Follow-up | 12.9 | 12.0 | 4.1 | 7 | 25 |
| Terse | 8.5 | 8.0 | 2.9 | 3 | 16 |

Styles separate cleanly on length. Conversational questions are 3.6× longer than terse ones on average. Personal context questions show the highest within-style variance (stdev 7.0), reflecting varied amounts of situational detail users provide. Grammatical questions cluster tightly (stdev 2.6), consistent with a standard interrogative sentence pattern.

---

## 3. Formality & Punctuation

### 3.1 All-lowercase rate

A strong proxy for informality — typed without capitalisation, as people do on mobile.

| Style | All-lowercase |
|---|---:|
| Terse | **100%** |
| Typo | 95.1% |
| Follow-up | 92.1% |
| Conversational | 45.7% |
| Personal context | 28.8% |
| Grammatical | **6.7%** |

Terse and typo questions are almost universally lowercase. Grammatical questions are almost always properly capitalised. This is the sharpest single-feature separator between formal and informal styles.

### 3.2 Question mark rate

| Style | Has `?` |
|---|---:|
| Grammatical | **91.7%** |
| Conversational | 74.3% |
| Personal context | 73.1% |
| Follow-up | 5.3% |
| Terse | **0.0%** |
| Typo | **0.0%** |

Terse and typo queries carry no terminal punctuation — they read as keyword searches. Follow-up questions also mostly omit the `?`, mirroring how people phrase continuations in a chat thread ("what if i already submitted" rather than "What if I already submitted?").

### 3.3 Multi-sentence questions

| Style | Multi-sentence |
|---|---:|
| Conversational | 28.6% |
| Personal context | 26.9% |
| All others | 0.0% |

Only conversational and personal-context questions span multiple sentences. Conversational questions often open with a contextual statement before the actual ask; personal-context questions provide situation detail then end with a question.

---

## 4. Person & Voice

### 4.1 First-person usage (contains I / my / we / our)

| Style | First-person |
|---|---:|
| Conversational | **100%** |
| Personal context | **100%** |
| Follow-up | 94.7% |
| Terse | 71.2% |
| Typo | 70.7% |
| Grammatical | 61.7% |

First-person is near-universal across all styles, reflecting the disaster context — users are asking about their own situation. Even grammatical questions (e.g. "How do I apply for FEMA assistance?") are predominantly self-referential.

### 4.2 Starts with a question word (how / what / where / when / why / can / do)

| Style | Starts w/ question word |
|---|---:|
| Grammatical | **98.3%** |
| Typo | 75.6% |
| Terse | 65.0% |
| Follow-up | 55.3% |
| Personal context | 5.8% |
| Conversational | **2.9%** |

Grammatical questions almost always open with a question word. Conversational questions rarely do — they typically open with "hi", "I'm", or "my house" instead. The 15 most common opening words across all questions reflect this divide:

| Opener | Count | Opener | Count |
|---|---:|---|---:|
| how | 45 | i | 26 |
| hi | 33 | my | 25 |
| can | 31 | i'm | 23 |
| what | 31 | do | 17 |

"Hi" as the second most common opener (33 occurrences) is a conversational-style signal — users greeting a chatbot before asking their question.

---

## 5. Informality Signals

### 5.1 Typo / informal spelling detection

The typo detector looks for a set of known misspellings and contractions run together (`cant`, `dont`, `im `, `aproval`, `insuarance`, etc.).

| Style | Typo signal detected |
|---|---:|
| Personal context | 11.5% |
| Typo | **7.3%** |
| Conversational | 8.6% |
| Follow-up | 7.9% |
| Terse | 5.0% |
| Grammatical | **1.7%** |

The typo-style questions have a **lower** detected rate than personal-context or conversational. This is a limitation of keyword-based detection — the generator produces varied misspellings (e.g. `recieve`, `loosing`, `goverment`) that are not all captured by the fixed word list. A spellcheck-based approach (e.g. `pyspellchecker`) would give higher signal. Despite this, the overall rate of 6.0% (18/306 questions) represents a realistic background level of typing errors in chatbot traffic.

### 5.2 Informal phrasing (`hi`, `hey`, `pls`, `help me`, `what do i do`, etc.)

| Style | Informal signal |
|---|---:|
| Conversational | **91.4%** |
| Terse | 8.8% |
| Follow-up | 15.8% |
| Typo | 2.4% |
| Personal context | 5.8% |
| Grammatical | **0.0%** |

Conversational questions almost always include an informal opener or filler phrase. Grammatical questions have none.

---

## 6. Vocabulary

### 6.1 Corpus-level statistics

| Metric | Value |
|---|---|
| Total tokens | 4,534 |
| Unique types | 853 |
| Type-token ratio (TTR) | 0.188 |

A TTR of 0.188 is typical for a domain-specific corpus with repeated terminology. FEMA, fire, disaster, insurance, and apply appear frequently by design.

### 6.2 Top domain terms

The 20 most frequent content words (excluding stopwords) reveal the topic distribution is well-grounded in the actual disaster recovery domain:

`fema` (63) · `fire` (45) · `get` (43) · `after` (40) · `apply` / `applied` · `insurance` · `home` · `help` · `disaster` · `lost` · `housing` · `assistance` · `claim` · `damaged`

### 6.3 Numbers in questions

| Style | Contains a number |
|---|---:|
| Conversational | 22.9% |
| Personal context | 19.2% |
| Follow-up | 18.4% |
| Terse | 2.5% |
| Typo | 4.9% |
| Grammatical | **0.0%** |

Numbers appear in the longer, narrative styles — typically dollar amounts, days/weeks, or addresses embedded in context ("I lost about $10,000 in belongings"). Terse and grammatical questions are almost entirely number-free.

---

## 7. Style × Tier Cross-Tabulation

Each tier's style mix differs, which is appropriate: high-urgency tier-1 questions skew toward terse and follow-up (people in crisis mode); long-tail tier-4 questions skew toward conversational and personal-context (niche situations that require more explanation).

| Style | Tier 1 Critical | Tier 2 High-vol | Tier 3 Moderate | Tier 4 Long-tail |
|---|---:|---:|---:|---:|
| Terse | 22 | 28 | 16 | 14 |
| Grammatical | 16 | 18 | 13 | 13 |
| Personal context | 13 | 17 | 10 | 12 |
| Typo | 9 | 13 | 8 | 11 |
| Follow-up | 12 | 12 | 9 | 5 |
| Conversational | 8 | 8 | 8 | 11 |
| **Total** | **80** | **96** | **64** | **66** |

---

## 8. Summary Findings

**Styles are linguistically well-separated.** The six style labels are not cosmetic — they correspond to genuine differences in length, capitalisation, punctuation, and phrasing that a real user population would exhibit.

**Terse and typo questions are the most informal.** They are 100% lowercase and carry no terminal punctuation, matching how people type keyword-style queries on mobile.

**Conversational questions are longest and most context-rich.** At a mean of 30.8 words with 91% containing an informal opener, they most closely mimic the "hi, I have a situation" pattern of real chatbot conversations.

**Grammatical questions are tightly clustered.** Low variance in length (stdev 2.6), 98% start with a question word, 92% end with `?`, 0% informal signals. These are the easiest for a chatbot to parse correctly and represent the ceiling of input quality.

**First-person dominates across all styles (78% overall).** The disaster context makes this expected — users are always asking about their own situation, not seeking general encyclopedic information.

**The typo-detection rate underestimates actual variation.** The keyword-based approach only captures 7% of the typo-labelled questions. A fuller analysis using a spellchecker would surface more variation in that style cohort.

---

*Generated from `qa_pairs.json` (306 questions, 34 topics, 6 styles).*
