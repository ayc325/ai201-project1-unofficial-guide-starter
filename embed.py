"""
embed.py — Embed all chunks and store them in ChromaDB. Provides a retrieve() function.

Pipeline position: chunk.py → embed.py → (retrieval) → generation

Usage:
  python embed.py                        # build the index
  python embed.py --rebuild              # wipe and re-index from scratch
  python embed.py --query "your query"  # build index then run a test query
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

import chromadb
from sentence_transformers import SentenceTransformer

from chunk import DOCUMENTS_DIR, Chunk, chunk_file

CHROMA_PATH = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "lego_ideas_retirement"
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5

# Module-level singletons — loaded once, reused across calls to retrieve()
_model: Optional[SentenceTransformer] = None
_collection = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"Loading {EMBED_MODEL}...")
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def _get_collection(client: Optional[chromadb.PersistentClient] = None):
    global _collection
    if _collection is None:
        if client is None:
            client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},  # use cosine similarity, not L2
        )
    return _collection


# ── Indexing ─────────────────────────────────────────────────────────────────

def build_index(rebuild: bool = False) -> None:
    """Load all chunks, embed them, and upsert into ChromaDB."""
    global _collection

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    if rebuild:
        # Delete the old collection entirely so stale chunks don't linger
        try:
            client.delete_collection(COLLECTION_NAME)
            print("Deleted existing collection.")
        except Exception:
            pass
        _collection = None  # reset the cached reference

    collection = _get_collection(client)

    if not rebuild and collection.count() > 0:
        print(f"Index already has {collection.count()} chunks. Pass --rebuild to re-index.")
        return

    # Load all chunks from every .txt file in documents/
    txt_files = sorted(DOCUMENTS_DIR.glob("*.txt"))
    all_chunks: list[Chunk] = []
    for path in txt_files:
        file_chunks = chunk_file(path)
        all_chunks.extend(file_chunks)
        print(f"  {path.name}: {len(file_chunks)} chunks")

    if not all_chunks:
        sys.exit("No chunks produced. Check that documents/*.txt files exist.")

    print(f"\nEmbedding {len(all_chunks)} chunks with {EMBED_MODEL}...")
    model = _get_model()
    embeddings = model.encode(
        [c.text for c in all_chunks],
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    # Each chunk gets a stable ID: "<source>__chunk_<index>"
    # This means upsert is idempotent — re-running won't duplicate records.
    collection.upsert(
        ids=[f"{c.source}__chunk_{c.index}" for c in all_chunks],
        embeddings=embeddings.tolist(),
        documents=[c.text for c in all_chunks],
        metadatas=[
            {"source": c.source, "chunk_index": c.index, "strategy": c.strategy}
            for c in all_chunks
        ],
    )

    print(f"\nStored {collection.count()} chunks in {CHROMA_PATH}/")


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """
    Embed a query string and return the top-k most similar chunks.

    Returns a list of dicts, each with:
      text      — the chunk's full text
      source    — source filename (e.g. "brick_tap_retirement_dates.txt")
      index     — chunk's position within that file
      strategy  — chunking strategy that produced this chunk
      distance  — cosine distance (0 = identical, 2 = opposite; lower is better)
    """
    model = _get_model()
    collection = _get_collection()

    query_vec = model.encode(query, convert_to_numpy=True).tolist()

    results = collection.query(
        query_embeddings=[query_vec],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "text": text,
            "source": meta["source"],
            "index": meta["chunk_index"],
            "strategy": meta["strategy"],
            "distance": round(dist, 4),
        })
    return hits


# ── Main (test harness) ───────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Build ChromaDB index and test retrieval.")
    parser.add_argument("--rebuild", action="store_true", help="Wipe and re-index from scratch.")
    parser.add_argument("--query", type=str, help="Run a single test query after indexing.")
    args = parser.parse_args()

    build_index(rebuild=args.rebuild)

    # Evaluation queries from planning.md
    test_queries = [
        args.query,
        "When does the Jaws set retire?",
        "In what waves do LEGO retirements occur?",
        "What happens to LEGO set prices after retirement?",
        "What does the official LEGO store mark on sets that are retiring soon?",
        "Is there a spreadsheet that tracks LEGO retirement dates?",
    ]
    test_queries = [q for q in test_queries if q]  # drop None if --query not passed

    print()
    for query in test_queries:
        print(f"Query: {query!r}")
        print("─" * 60)
        for hit in retrieve(query):
            preview = hit["text"][:180].replace("\n", " ").strip()
            print(f"  [{hit['distance']:.4f}]  {hit['source']}  (chunk {hit['index']})")
            print(f"           {preview}")
            print()
        print()


if __name__ == "__main__":
    main()
