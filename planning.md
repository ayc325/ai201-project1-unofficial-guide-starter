# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
     Retiring LEGO IDEAS sets are useful to track because once LEGO announces a set is retiring, remaining retail stock often disappears quickly, making the set harder to find at regular prices.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | LEGO Official Website | Official LEGO Website | https://www.lego.com/en-us/categories/last-chance-to-buy?filters.i0.key=categories.id&filters.i0.values.i0=2237887c-51ec-4e65-becf-117ae6180bf0 |
| 2 | Stone Wars | LEGO News Site | https://stonewars.com/retiring-2026/#lego-ideas |
| 3 | Brick Fanatics | LEGO News Site | https://www.brickfanatics.com/every-lego-set-retiring-this-year-and-beyond#retiring-lego-ideas-sets |
| 4 | Brick Tap - LEGO Ideas - All upcoming sets (Update soon) | CSV | "Brick Tap - LEGO Ideas - All upcoming sets (Update soon)".csv |
| 5 | BrickLink FAQ | FAQ Page | https://www.bricklink.com/v3/designer-program/faq.page |
| 6 | Brick Tap - LEGO Set List - Retirement Dates + Store Exclusivity | Google Sheets | https://docs.google.com/spreadsheets/d/1rlYfEXtNKxUOZt2Mfv0H17DvK7bj6Pe0CuYwq6ay8WA/edit?usp=sharing |
| 7 | Can you predict which sets retire when? | Reddit post | https://www.reddit.com/r/lego/comments/1cfflb2/can_you_predict_which_sets_retire_when/ |
| 8 | New to the hobby, curious to find out when sets retire | Reddit post | https://www.reddit.com/r/lego/comments/1l1tm77/new_to_the_hobby_curious_to_find_out_when_sets/ |
| 9 | Brick Economy | URL | https://www.brickeconomy.com/sets/retiring-soon |
| 10 | The Complete Guide to LEGO Set Retirement: What it means for Collectors | URL | https://bamgoodbricks.com/blogs/lego-news/the-complete-guide-to-lego%C2%AE-set-retirement-what-it-means-for-collectors |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->
     - Hybrid Chunking

**Chunk size:**
     - Structured data (CSV, Sheets, product listings): Fixed-size with row-boundary alignment — never split mid-row. ~1 row per chunk, or batch small rows together up to ~150 tokens (staying within all-MiniLM-L6-v2's 256-token limit).
     - FAQ: Semantic — one Q+A pair per chunk. These are already naturally segmented.
     - Articles/prose: Recursive — split by heading → paragraph → sentence. This respects the document's own hierarchy and avoids the waste of fixed-size cutting through a paragraph mid-thought.
     - Reddit threads: Semantic — one top-level comment (plus direct replies) per chunk, since a comment only makes sense with its immediate context.
**Overlap:**
     - 50-75 tokens
**Reasoning:**
     - Pure fixed-size cuts through table rows and FAQ answers, corrupting retrieval.
     Pure semantic (embedding-similarity-based) is computationally heavy and overkill for data that already has explicit structure (CSV rows, FAQ boundaries).
     Pure recursive works for prose but produces oddly-shaped chunks from tabular data.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**
     - all-MiniLM-L6-v2
**Top-k:**
     - 7 (increased from 5 — date-specific queries need the extra window to surface the right retirement date chunk alongside similar-scoring chunks from other dates)
**Production tradeoff reflection:**
     - Context length: text-embedding-3-large (OpenAI) or embed-english-v3.0 (Cohere) handle longer chunks without truncation
     - Domain accuracy: a model fine-tuned on product/retail text would handle set names and part numbers better
     - Latency: all-MiniLM-L6-v2 runs locally and is fast; larger models add API round-trip latency
     - Some inaccuracy is ok because there's no harm in the LLM predicting a LEGO set that may retire this year vs next year since all LEGO sets eventually retire
---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | When does the Jaws set retire? | July 31, 2026 |
| 2 | In what waves do LEGO retirmenets occur in? | January, June/July, and December |
| 3 | What happens to LEGO set prices after retirement? | Some go up, some stay flat, some decrease. |
| 4 | What does the official LEGO store mark on sets that are retiring soon? | Last Chance to Buy or Retiring Soon |
| 5 | Is there a spreadsheet that tracks LEGO retirement dates? | Yes, Brick Tap does. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. Some documents are noisy since it's not JUST LEGO IDEAS sets and have a bunch of like header/footer/ads etc..

2. Various file types that may struggle with the various chunking styles

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  1. INGESTION    │  │  2. CHUNKING     │  │  3. EMBEDDING +      │  │  4. RETRIEVAL    │  │  5. GENERATION   │
│                  │─▶│                  │─▶│     VECTOR STORE     │─▶│                  │─▶│                  │
│  requests/BS4    │  │  Fixed-size      │  │  all-MiniLM-L6-v2    │  │  cosine sim      │  │  Claude API      │
│  pandas - CSV    │  │  (CSV, Sheets,   │  │  sentence-           │  │  top-k = 5       │  │  (claude-sonnet) │
│  PRAW - Reddit   │  │   listings)      │  │  transformers        │  │                  │  │                  │
│                  │  │  Semantic        │  │  ChromaDB            │  │                  │  │                  │
│                  │  │  (FAQ, Reddit)   │  │                      │  │                  │  │                  │
│                  │  │  Recursive       │  │                      │  │                  │  │                  │
│                  │  │  (articles)      │  │                      │  │                  │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

     - I'll give Claude my Chunking Strategy section along with the information of the strategies I'm allowed to use and ask it to implement chunk_text() with the specified chunk size and overlap for each type of source.
     - I'll give Claude the sources in my Documents section to clean up uncessary information to clean up and refine for better information on the embedding and retrieval step.

**Milestone 3 — Ingestion and chunking:**

- Reduced max chunk size from ~300 to ~150 tokens to stay safely under the embedding model's 256-token hard limit and produce more focused, retrievable chunks.
- Structured data (CSV rows) were originally kept as raw tab-separated text, which embedded poorly against natural language queries. Fixed by converting each row to a prose sentence before chunking.
- `bricklink_faq.txt` was trimmed from 16 pages to a single Q&A covering only the LEGO IDEAS vs. BrickLink Designer Program distinction, which is the only content relevant to this project.
- `brick_tap_ideas.txt` was cleaned to remove rows where the release date was TBA, keeping only the 2 sets with confirmed release dates (21365, 21366).
- Retirement date rows were later regrouped by retirement date (in Milestone 4) after testing showed individual rows produced structurally identical embeddings that didn't rank by date.

**Milestone 4 — Embedding and retrieval:**

Used `embed.py` with `all-MiniLM-L6-v2` via sentence-transformers to embed all chunks and store them in ChromaDB with source metadata (filename, chunk index, strategy). Key changes made during implementation:

- Structured data chunks were originally formatted as raw tab-separated rows, which embedded poorly against natural language queries. Fixed by converting each row to a natural language sentence in `chunk.py` (e.g. "LEGO Ideas set 21348, Dungeons & Dragons: Red Dragon's Tale, retires July 31, 2026.").
- Month abbreviations ("Jul", "Dec") were expanded to full names so query phrasing like "July 31, 2026" matches chunk text exactly.
- Retirement date rows were regrouped by date rather than one-row-per-chunk, so a query like "which sets retire by July 31, 2026?" retrieves a single chunk listing all sets for that date instead of competing against 25 structurally identical rows.
- Top-k increased from 5 to 7 after testing showed the correct retirement date chunk landing at rank 6 for date-specific queries.

**Milestone 5 — Generation and interface:**

Used Groq (`llama-3.3-70b-versatile`) in `query.py` for generation. The prompt passes retrieved chunks as numbered context blocks and instructs the model to answer only from those documents, cite sources, and say "I don't have enough information" if the context is insufficient. Built a Gradio interface in `app.py` with a preset question dropdown (matching the 5 evaluation questions from the Evaluation Plan) and a free-text input. Answers and retrieved source filenames are displayed separately so responses are traceable.
