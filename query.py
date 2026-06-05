"""
query.py — End-to-end RAG function: retrieve relevant chunks, then generate with Groq.

Pipeline position: embed.py (retrieve) → query.py (generate) → app.py (interface)
"""

import os

from dotenv import load_dotenv
from groq import Groq

from embed import retrieve

load_dotenv()

MODEL = "llama-3.3-70b-versatile"
TOP_K = 7

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client


def ask(question: str, k: int = TOP_K) -> dict:
    """
    Run the full RAG pipeline for a single question.

    Returns:
      answer  — LLM response grounded in retrieved chunks
      sources — deduplicated list of source filenames used
      chunks  — the raw retrieved chunks (for debugging)
    """
    hits = retrieve(question, k=k)

    # Build a numbered context block so the model can cite specific sources
    context_blocks = []
    for i, hit in enumerate(hits, 1):
        context_blocks.append(f"[Source {i} — {hit['source']}]\n{hit['text']}")
    context = "\n\n".join(context_blocks)

    prompt = (
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
    )

    response = _get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )

    answer = response.choices[0].message.content

    # Deduplicate sources while preserving retrieval order
    seen: set[str] = set()
    sources: list[str] = []
    for hit in hits:
        if hit["source"] not in seen:
            seen.add(hit["source"])
            sources.append(hit["source"])

    return {"answer": answer, "sources": sources, "chunks": hits}


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "When does the Jaws set retire?"
    result = ask(q)
    print(result["answer"])
    print("\nSources:", ", ".join(result["sources"]))
