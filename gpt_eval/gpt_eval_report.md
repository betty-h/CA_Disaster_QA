# CA Disaster Recovery Chatbot — Evaluation Report

**Predictions file:** `data/predictions.jsonl`  
**Pairs evaluated:** 305  
**Evaluation failures:** 0  

---

## Overall Score

**Mean weighted score: 3.531 / 5.000**

### Rubric weights

| Dimension | Weight | Mean Score |
|-----------|-------:|----------:|
| Factual Accuracy | 30% | 3.34 |
| Completeness | 20% | 2.75 |
| Actionability | 20% | 4.09 |
| Tone & Empathy | 10% | 3.91 |
| Conciseness | 10% | 4.08 |
| Hallucination (inverse) | 10% | 3.60 |

---

## Scores by Tier

| Tier | N | Mean Weighted Score |
|------|--:|--------------------:|
| tier_1_critical | 80 | 3.792 |
| tier_2_high_volume | 96 | 3.475 |
| tier_3_moderate | 64 | 3.522 |
| tier_4_long_tail | 65 | 3.300 |

## Scores by Question Style

| Style | N | Mean Weighted Score |
|-------|--:|--------------------:|
| conversational | 35 | 3.446 |
| follow_up | 38 | 3.616 |
| grammatical | 60 | 3.660 |
| personal_context | 52 | 3.285 |
| terse | 79 | 3.581 |
| typo | 41 | 3.551 |

---

## Lowest-Scoring Pairs (bottom 10)

**Score: 1.700** | Topic: Food and water assistance (CalFresh, food banks) | Style: typo
> **Q:** how long does it take to get aproved for calfesh
> **Gold:** Regular CalFresh applications are processed within 30 days, but if you have very low income and resources you may qualif
> **Predicted:** The California Fire Emergency Support Helpline (CalFESH) typically processes applications for assistance within 30 days.
> *The candidate misinterprets CalFresh as a fictional fire helpline and fabricates contact details, making it dangerously misleading for a user seeking food assistance.*

**Score: 1.900** | Topic: SBA disaster loans for homeowners and businesses | Style: terse
> **Q:** can sba loan be used for upgrades or just repairs
> **Gold:** SBA disaster loans generally can't be used to upgrade or add to your home — only to restore it to pre-disaster condition
> **Predicted:** SBA loans can be used for both repairs and upgrades to your property. Specifically, the SBA 7(a) loan program allows for
> *The candidate answer fundamentally misidentifies the loan program and gives incorrect information about what SBA disaster loans cover, despite being well-formatted.*

**Score: 1.900** | Topic: Filing insurance claims after a disaster | Style: grammatical
> **Q:** How long do I have to rebuild before insurance stops paying?
> **Gold:** Under California law, after a declared disaster you have at least 36 months to rebuild and collect full replacement cost
> **Predicted:** In California, the timeline for insurance payments during the rebuilding process can vary based on your specific policy.
> *The answer is dangerously inaccurate — it understates the rebuild window by years and could cause a disaster victim to forfeit benefits they are legally entitled to.*

**Score: 1.900** | Topic: FEMA appeals process | Style: personal_context
> **Q:** I'm 72 and I'm not great with computers — can someone help me file my appeal in person?
> **Gold:** Yes, you can take your appeal documents in person to a Disaster Recovery Center (DRC), where staff can help you submit t
> **Predicted:** Yes, you can get in-person assistance to file your appeal. The California Department of Social Services (CDSS) has local
> *The response is empathetic and well-structured but directs the user to the wrong agency (CDSS) for filing a FEMA appeal, making it factually misleading and unhelpful.*

**Score: 2.000** | Topic: Tax filing extensions and disaster tax relief | Style: terse
> **Q:** do i need to apply for the irs extension
> **Gold:** No — the IRS applies disaster relief automatically based on the address on your most recent tax return. If you moved int
> **Predicted:** Yes, if you need more time to file your federal tax return, you must apply for an IRS extension. You can do this by fili
> *The candidate answers a different question (general extension filing) rather than disaster-specific IRS relief, missing the critical automatic-relief point and the dedicated disaster hotline.*

**Score: 2.100** | Topic: Tax filing extensions and disaster tax relief | Style: follow_up
> **Q:** I filed for the disaster extension months ago and still haven't heard back, is that normal?
> **Gold:** You shouldn't expect a confirmation letter — disaster relief is applied automatically to your account based on your addr
> **Predicted:** It can take some time to process disaster extension applications, but if you haven't heard back in several months, it ma
> *The candidate misinterpreted the question as a FEMA/CalOES disaster assistance application rather than an IRS tax filing extension, leading to fundamentally wrong guidance despite a pleasant tone.*

**Score: 2.100** | Topic: Filing insurance claims after a disaster | Style: grammatical
> **Q:** What is the deadline to file a homeowners insurance claim after a wildfire in California?
> **Gold:** California law requires insurers to give you at least 12 months from the date of loss to file a claim after a declared d
> **Predicted:** In California, the deadline to file a homeowners insurance claim after a wildfire is typically set by your insurance pol
> *The answer is concise and points to CDI, but contains significant factual fabrications about deadlines that could seriously mislead a disaster survivor.*

**Score: 2.100** | Topic: Tax filing extensions and disaster tax relief | Style: personal_context
> **Q:** I'm a small business owner in Altadena, my shop was destroyed. Does the tax extension cover my quarterly estimated taxes
> **Gold:** Yes. The California wildfire relief covers individual and business returns, quarterly estimated tax payments, payroll an
> **Predicted:** I'm sorry to hear about the destruction of your shop. In California, if you qualify for a tax extension due to a disaste
> *The candidate answer is factually misleading on the central question, telling the business owner the opposite of the truth, and directs them to the wrong agency (CDTFA) rather than the IRS disaster hotline.*

**Score: 2.200** | Topic: Emotional support for children after a disaster | Style: grammatical
> **Q:** Are there free counseling services for children affected by California wildfires?
> **Gold:** Yes. FEMA's Crisis Counseling Assistance and Training Program (CCP) funds free, confidential counseling for disaster sur
> **Predicted:** Yes, there are free counseling services available for children affected by California wildfires. The California Departme
> *The response has appropriate tone and length but contains fabricated program/agency names and a misattributed phone number, while missing the key real resources (FEMA CCP, SAMHSA Disaster Distress Helpline, CalHOPE).*

**Score: 2.200** | Topic: Tax filing extensions and disaster tax relief | Style: terse
> **Q:** do i still have to file taxes by april 15 if my house burned down
> **Gold:** No. If you live in a federally declared California wildfire disaster area, the IRS has automatically postponed your fili
> **Predicted:** Yes, you still need to file your taxes by April 15, even if your house burned down. However, you may qualify for certain
> *The candidate gives the opposite of the correct answer by failing to mention the automatic IRS disaster extension, which is the critical piece of information for the user.*

---

## Dimension Definitions

### Factual Accuracy
Are the facts, program names, eligibility rules, phone numbers, and URLs in the evaluated answer correct relative to the gold answer and general knowledge of CA/federal disaster recovery programs? Penalise wrong agency names, wrong phone numbers, wrong eligibility rules.
*Scale:* 1 = multiple factual errors  |  3 = mostly correct, minor slip  |  5 = fully accurate

### Completeness
Does the evaluated answer cover the core informational needs expressed in the question and present in the gold answer? A complete answer need not be exhaustive — it must not omit the most critical point(s).
*Scale:* 1 = misses the main point  |  3 = covers main point, misses secondary  |  5 = fully covers the question

### Actionability
Does the answer give the user at least one clear, concrete next step (e.g., a URL to visit, a number to call, a form to file)? Disaster victims need to know what to DO, not just what exists.
*Scale:* 1 = no actionable guidance  |  3 = vague guidance  |  5 = clear, specific next step(s)

### Tone & Empathy
Is the tone appropriate for a stressed, possibly grieving disaster victim? It should be warm but efficient — not cold/bureaucratic, not excessively verbose, and not dismissive. Penalise clinical jargon without explanation and unnecessary caveats that delay the useful information.
*Scale:* 1 = cold/dismissive/jargon-heavy  |  3 = neutral  |  5 = warm, clear, and efficient

### Conciseness
Is the response an appropriate length for a chatbot reply? Target: 2–6 sentences. Penalise unnecessary padding, repeated information, or walls of text. Also penalise answers so short they omit essential info (that would be captured by the Completeness dimension too).
*Scale:* 1 = far too long or far too short  |  3 = acceptable  |  5 = ideal chatbot length

### Hallucination (inverse)
Does the answer introduce specific claims that are NOT in the gold answer AND are not verifiable general knowledge — e.g., invented dollar amounts, fabricated program names, made-up deadlines? NOTE: this dimension is scored inversely — 5 means NO hallucinations.
*Scale:* 1 = clear fabrications  |  3 = one uncertain/unverifiable claim  |  5 = no hallucinations
