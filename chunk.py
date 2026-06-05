"""
chunk.py — Apply the hybrid chunking strategy from planning.md to all .txt files in documents/.

Strategy routing:
  brick_tap_*.txt   → fixed-size, row-boundary aligned, header prepended per chunk
  bricklink_faq.txt → semantic, one Q+A pair per chunk
  reddit_*.txt      → semantic, one comment/paragraph block per chunk
  *_retiring.txt,
  *guide.txt        → recursive, paragraph → sentence, 60-token overlap
"""

import re
from dataclasses import dataclass
from pathlib import Path

DOCUMENTS_DIR = Path(__file__).parent / "documents"
MAX_TOKENS = 150     # safe margin under all-MiniLM-L6-v2's 256-token limit
OVERLAP_TOKENS = 50  # low end of the 50-75 token overlap spec (fits smaller chunks)

STRUCTURED_FILES = {"brick_tap_ideas.txt", "brick_tap_retirement_dates.txt"}
FAQ_FILES        = {"bricklink_faq.txt"}
REDDIT_FILES     = {"reddit_prediction_retirement.txt", "reddit_new_hobby.txt"}
PROSE_FILES      = {
    "brick_fantatics_retiring.txt",
    "brick_economy_retiring.txt",
    "lego_shop_retiring.txt",
    "stone_wars_retiring.txt",
    "bamgoodbricks_guide.txt",
}


@dataclass
class Chunk:
    text: str
    source: str
    index: int
    strategy: str


def est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


# ── Structured (CSV / Sheets) ────────────────────────────────────────────────

def chunk_structured(text: str, source: str) -> list[Chunk]:
    lines = text.splitlines()

    # Header = first line with at least 3 non-empty tab-separated cells.
    # This skips metadata rows (e.g. the "Check out Brick Tap…" line in
    # brick_tap_ideas.txt that only has 2 non-empty cells).
    header = ""
    data_start = 0
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.split("\t") if c.strip()]
        if len(cells) >= 3:
            header = line.strip()
            data_start = i + 1
            break

    data_lines = []
    for line in lines[data_start:]:
        stripped = line.strip()
        # Skip blank lines and section-header rows (e.g. "Ideas Pipeline")
        # that have no meaningful tab-separated data cells.
        if not stripped:
            continue
        cells = [c.strip() for c in stripped.split("\t") if c.strip()]
        if len(cells) < 2:
            continue
        data_lines.append(stripped)

    header_tokens = est_tokens(header)
    chunks: list[Chunk] = []
    batch: list[str] = []
    batch_tokens = 0

    for line in data_lines:
        lt = est_tokens(line)
        if batch and header_tokens + batch_tokens + lt > MAX_TOKENS:
            chunks.append(Chunk(
                text=header + "\n" + "\n".join(batch),
                source=source,
                index=len(chunks),
                strategy="fixed-size",
            ))
            batch = []
            batch_tokens = 0
        batch.append(line)
        batch_tokens += lt

    if batch:
        chunks.append(Chunk(
            text=header + "\n" + "\n".join(batch),
            source=source,
            index=len(chunks),
            strategy="fixed-size",
        ))

    return chunks


# ── FAQ ──────────────────────────────────────────────────────────────────────

_BROWSER_CHROME = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}.*\d:\d{2}\s+[AP]M", re.I)


def chunk_faq(text: str, source: str) -> list[Chunk]:
    blocks = re.split(r"\n{2,}", text.strip())
    chunks: list[Chunk] = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Drop page markers, browser chrome, and bare URLs
        if block.startswith("---") or _BROWSER_CHROME.match(block) or block.startswith("http"):
            continue
        if len(block) < 20:
            continue
        chunks.append(Chunk(block, source, len(chunks), "semantic-faq"))
    return chunks


# ── Prose (articles) ─────────────────────────────────────────────────────────

_REDDIT_SIDEBAR = re.compile(
    r"/r/lego is about|r/LEGO MISSION STATEMENT|Created \w+ \d+, \d{4}|"
    r"Weekly Brick Fan|Official LEGO® Sites|Join\s+\d[\d,.]+\s+members",
    re.I,
)


def _clean_prose(text: str) -> str:
    text = re.sub(r"--- Page \d+ ---", "\n", text)
    text = re.sub(r"\d{1,2}/\d{1,2}/\d{2,4}[^\n]*\d:\d{2}\s+[AP]M[^\n]*", "", text, flags=re.I)
    text = re.sub(r"https?://\S+", "", text)
    # Strip Reddit sidebar fragments that bleed into extracted text
    text = _REDDIT_SIDEBAR.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _fit_to_chunks(paragraphs: list[str]) -> list[str]:
    raw: list[str] = []
    for para in paragraphs:
        if est_tokens(para) <= MAX_TOKENS:
            raw.append(para)
        else:
            sentences = _split_sentences(para)
            current = ""
            for sent in sentences:
                candidate = (current + " " + sent).strip()
                if est_tokens(candidate) > MAX_TOKENS and current:
                    raw.append(current)
                    current = sent
                else:
                    current = candidate
            if current:
                raw.append(current)
    return raw


def chunk_prose(text: str, source: str) -> list[Chunk]:
    text = _clean_prose(text)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip() and len(p.strip()) >= 30]
    raw = _fit_to_chunks(paragraphs)

    chunks: list[Chunk] = []
    for i, block in enumerate(raw):
        if i > 0:
            prev = raw[i - 1]
            overlap_chars = OVERLAP_TOKENS * 4
            overlap = (prev[-overlap_chars:] if len(prev) > overlap_chars else prev).strip()
            block = overlap + "\n" + block
        chunks.append(Chunk(block.strip(), source, i, "recursive"))

    return chunks


# ── Reddit ───────────────────────────────────────────────────────────────────

def chunk_reddit(text: str, source: str) -> list[Chunk]:
    text = _clean_prose(text)
    blocks = [b.strip() for b in text.split("\n\n") if b.strip() and len(b.strip()) >= 40]

    chunks: list[Chunk] = []
    for block in blocks:
        if est_tokens(block) <= MAX_TOKENS:
            chunks.append(Chunk(block, source, len(chunks), "semantic-reddit"))
        else:
            sentences = _split_sentences(block)
            current = ""
            for sent in sentences:
                candidate = (current + " " + sent).strip()
                if est_tokens(candidate) > MAX_TOKENS and current:
                    chunks.append(Chunk(current, source, len(chunks), "semantic-reddit"))
                    current = sent
                else:
                    current = candidate
            if current:
                chunks.append(Chunk(current, source, len(chunks), "semantic-reddit"))

    return chunks


# ── Router ───────────────────────────────────────────────────────────────────

def chunk_file(path: Path) -> list[Chunk]:
    text = path.read_text(encoding="utf-8")
    name = path.name
    if name in STRUCTURED_FILES:
        return chunk_structured(text, name)
    if name in FAQ_FILES:
        return chunk_faq(text, name)
    if name in REDDIT_FILES:
        return chunk_reddit(text, name)
    if name in PROSE_FILES:
        return chunk_prose(text, name)
    return chunk_prose(text, name)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    txt_files = sorted(DOCUMENTS_DIR.glob("*.txt"))
    if not txt_files:
        print("No .txt files found in documents/")
        return

    all_chunks: list[Chunk] = []
    for path in txt_files:
        chunks = chunk_file(path)
        all_chunks.extend(chunks)
        print(f"  {path.name:<45} {len(chunks):>4} chunks")

    total = len(all_chunks)
    print(f"\nTotal: {total} chunks across {len(txt_files)} files")
    if total < 50:
        print("  WARNING: fewer than 50 chunks — chunks may be too large.")
    elif total > 2000:
        print("  WARNING: more than 2,000 chunks — consider batching rows more aggressively.")

    # 5 representative chunks — one per strategy, plus a mid-file retirement row
    print("\n" + "=" * 64)
    print("5 REPRESENTATIVE CHUNKS")
    print("=" * 64)

    seen_strategies: set[str] = set()
    sample: list[Chunk] = []
    for chunk in all_chunks:
        if chunk.strategy not in seen_strategies:
            seen_strategies.add(chunk.strategy)
            sample.append(chunk)
        if len(sample) == 4:
            break

    retirement_chunks = [c for c in all_chunks if c.source == "brick_tap_retirement_dates.txt"]
    if retirement_chunks:
        sample.append(retirement_chunks[len(retirement_chunks) // 2])

    for i, chunk in enumerate(sample, 1):
        print(f"\n[{i}] source={chunk.source}  strategy={chunk.strategy}  ~{est_tokens(chunk.text)} tokens")
        print("-" * 64)
        preview = chunk.text[:500]
        if len(chunk.text) > 500:
            preview += "\n... [truncated]"
        print(preview)

    print()


if __name__ == "__main__":
    main()
