# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

Retiring LEGO IDEAS sets are useful to track because once LEGO announces a set is retiring, remaining retail stock often disappears quickly, making the set harder to find at regular prices.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | LEGO Official Website | Official LEGO Website | https://www.lego.com/en-us/categories/last-chance-to-buy?filters.i0.key=categories.id&filters.i0.values.i0=2237887c-51ec-4e65-becf-117ae6180bf0 |
| 2 | Stone Wars | LEGO News Site | https://stonewars.com/retiring-2026/#lego-ideas |
| 3 | Brick Fanatics | LEGO News Site | https://www.brickfanatics.com/every-lego-set-retiring-this-year-and-beyond#retiring-lego-ideas-sets |
| 4 | Brick Tap - LEGO Ideas - All upcoming sets (Update soon) | CSV | "Brick Tap - LEGO Ideas - All upcoming sets (Update soon)".csv |
| 5 | BrickLink FAQ | FAQ Page | https://www.bricklink.com/v3/designer-program/faq.page |
| 6 | Brick Tap - LEGO Calendar - Promos, Sales and Point Events| Google Sheets | https://docs.google.com/spreadsheets/d/16muL-6LmJFG4SPnTKWLKOiFDBR2eMiijVyuiAusz_UE/edit?gid=232362826#gid=232362826 |
| 7 | Can you predict which sets retire when? | Reddit post | https://www.reddit.com/r/lego/comments/1cfflb2/can_you_predict_which_sets_retire_when/ |
| 8 | New to the hobby, curious to find out when sets retire | Reddit post | https://www.reddit.com/r/lego/comments/1l1tm77/new_to_the_hobby_curious_to_find_out_when_sets/ |
| 9 | Brick Economy | URL | https://www.brickeconomy.com/sets/retiring-soon |
| 10 | The Complete Guide to LEGO Set Retirement: What it means for Collectors | URL | https://bamgoodbricks.com/blogs/lego-news/the-complete-guide-to-lego%C2%AE-set-retirement-what-it-means-for-collectors |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

- Hybrid Chunking

**Chunk size:**

**Overlap:**

**Why these choices fit your documents:**

**Final chunk count:**

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**

**Production tradeoff reflection:**

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
