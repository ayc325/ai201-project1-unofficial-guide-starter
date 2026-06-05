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

**Chunk size: ~150 tokens**

**Overlap: 50 to 75 tokens**

**Why these choices fit your documents: Through the clean up process, the source of each file drastically got reduced. This led to it becoming smaller chunks which was originally 300 tokens. In addition, some overlap is required so that there is useful information in every chunk about retired sets.**

**Final chunk count: 76 chunks**

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used: all-MiniLM-L6-v2**

**Production tradeoff reflection:**
     - Context length: text-embedding-3-large (OpenAI) or embed-english-v3.0 (Cohere) handle longer chunks without truncation
     - Domain accuracy: a model fine-tuned on product/retail text would handle set names and part numbers better
     - Latency: all-MiniLM-L6-v2 runs locally and is fast; larger models add API round-trip latency
     - Some inaccuracy is ok because there's no harm in the LLM predicting a LEGO set that may retire this year vs next year since all LEGO sets eventually retire

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**
```
     "You are a helpful assistant for the Unofficial LEGO Ideas Retirement Guide.\n\n"
     "Rules:\n"
     "1. Answer ONLY using the documents provided below. Do not use any outside knowledge.\n"
     "2. Every factual claim must be attributed inline using the format: "
     "'According to [source: filename], ...'\n"
     "3. If multiple sources support a claim, cite each one.\n"
     "4. If the documents do not contain enough information to answer, respond with: "
     "'I don't have enough information on that in my sources.'\n"
     "5. Never guess, infer, or fill in details not explicitly stated in the documents.\n\n"
     f"Documents:\n{context}\n\n"
     f"Question: {question}"
```

**How source attribution is surfaced in the response:**
     - According to [source: stone_wars_retiring.txt], the 21350 Jaws set retires in 2026, 07. Additionally, According to [source: brick_economy_retiring.txt], the 21350 Jaws set is expected to retire at the End of 2026 with a 90.2% probability.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | When does the Jaws set retire? | July 31, 2026 | [source: stone_wars_retiring.txt], the 21350 Jaws set retires in 07 2026 | partially relevant | accurate
| 2 | In what waves do LEGO retirmenets occur in? | January, June/July, and December | [source: bamgoodbricks_guide.txt], ... in January, June/July, and December. | relevant | accurate
| 3 | What happens to LEGO set prices after retirement? | Some go up, some stay flat, some decrease. | some sets climb slowly over years, while others spike within months ... then see prices normalize ... some sets remain flat or decline in value after retirement. | relevant | accurate
| 4 | What does the official LEGO store mark on sets that are retiring soon? | Last Chance to Buy or Retiring Soon | once a set is marked as “Retiring Soon” or “Last Chance to Buy,” remaining stock can disappear quickly | partially relevant | accurate
| 5 | Is there a spreadsheet that tracks LEGO retirement dates? | Yes, Brick Tap does. | there is a spreadsheet linked in the Legoleak sub that tracks LEGO retirement dates | partially relevant | partially accurate, doesn't include the sheet name

**Retrieval quality:** Relevant / Partially relevant / Off-target
     - Relevant  
**Response accuracy:** Accurate / Partially accurate / Inaccurate
     - Accurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

 

**Question that failed & What the system returned:**

There was a specific test case to test when the Dungeons and Dragons set would retire. This prompt was answered correctly with the date July 2026. However, when asked what sets are retiring in July 2026, there were no valid answers and I would receive a response like "I have no information about sets retiring in 2026".

**Root cause (tied to a specific pipeline stage):**

The Top-K value being at 5 was not optimal as it didn't receive enough responses during the chunking stage. In addition, the LLM was missing semantic context for date abbreviations.

**What you would change to fix it:**

I had to add a helper function in chunk.py to consider date abbreviations and also had to increase the Top-K value to 7 so it took in more chunks. This change helped improve the response and receive an accurate response.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
Produced clear responses without wiggle room for error. It changed my view of programming w/ AI as my usual way usually leads to diverged answers. 

**One way your implementation diverged from the spec, and why:**
When I got frustrated with the failing test (now changed but also passes when tested again), I just told AI to "fix it" or "I'm not sure why this isn't working. Make changes to the corresponding files" which might've provided to many possible decision makings on Claude. The helper function portion was not part of the spec.

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
     - i feel like the distance for these aren't great... do you have other queries that might work well with the data from @documents/ ?
- *What it produced:*
     - Based on what's actually in your documents, here are queries that should score much better because the vocabulary matches the chunk text more directly:

     Specific set lookups — these will pull exact retirement date chunks:

     "When does the Jaws set retire?"
     "When does the Grand Piano LEGO set retire?"
     "What LEGO Ideas sets retire in December 2026?"
     Vocabulary that appears verbatim in bamgoodbricks_guide.txt:

     "What happens to LEGO set prices after retirement?"
     "What is the difference between a LEGO set retiring and being discontinued?"
     "Why do LEGO sets retire?"
- *What I changed or overrode:*
     - I followed through with the initial change, but kept trying the initial queries for testing.

**Instance 2**

- *What I gave the AI:*
     - I think I'm missing the interface portion of this pipeline diagram... I should have a list of questions that the user can select from a list where the LLM will be called and then return a structured/grounded, traceable response with the source. I am using Gradio with this sample code: 
     (Added the instructions for this from the project 1 instructions)
- *What it produced:*
     I'll build all three pieces in parallel — update planning.md diagram, create query.py (the ask() function), and create app.py (the Gradio interface), then update requirements.txt.
- *What I changed or overrode:*
     I declined all changes and rephrased the prompt to take it step by step. I started with the query, and then the app.py. Since it forgot about the planning.md, I had to tell it again to edit that as well.