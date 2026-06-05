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
#
# Raw tab-separated rows embed poorly — all-MiniLM-L6-v2 is trained on prose,
# so a query like "when does D&D retire?" won't match a tab-separated row even
# when that row has the exact answer. Converting each row to a natural language
# sentence before embedding fixes this.

_MONTH_ABBR = {
    "Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April",
    "May": "May",     "Jun": "June",     "Jul": "July",  "Aug": "August",
    "Sep": "September", "Oct": "October", "Nov": "November", "Dec": "December",
}

def _expand_date(date_str: str) -> str:
    """Expand abbreviated month names so queries using full names match exactly."""
    for abbr, full in _MONTH_ABBR.items():
        if date_str.startswith(abbr + " "):
            return full + date_str[len(abbr):]
    return date_str


def _row_to_prose_retirement(cols: dict[str, str]) -> str:
    """brick_tap_retirement_dates.txt row → natural language sentence."""
    theme    = cols.get("Theme", "").strip()
    subtheme = cols.get("Subtheme", "").strip().strip("-").strip()
    set_num  = cols.get("Set #", "").strip()
    name     = cols.get("Set Name", "").strip()
    pieces   = cols.get("Piece Count", "").strip()
    retire   = _expand_date(cols.get("Retirement Date", "").strip())
    notes    = cols.get("Notes: (Exclusivity, release, etc.)", "").strip()

    parts = [f"LEGO {theme} set {set_num}, {name}, retires {retire}."]
    if subtheme:
        parts.append(f"Subtheme: {subtheme}.")
    if pieces:
        parts.append(f"{pieces} pieces.")
    if notes:
        parts.append(notes)
    return " ".join(parts)


def _row_to_prose_ideas(cols: dict[str, str]) -> str:
    """brick_tap_ideas.txt row → natural language sentence."""
    set_num  = cols.get("Set #", "TBA").strip()
    name     = cols.get("Set Name", "").strip()
    pieces   = cols.get("Piece Count", "").strip()
    release  = cols.get("Release Date", "TBA").strip()
    price    = cols.get("Rumored Price", "").strip()
    notes    = cols.get("Notes", "").strip()

    label = f"set {set_num}" if set_num and set_num != "TBA" else "set (number TBA)"
    parts = [f"Upcoming LEGO Ideas {label}, {name}. Expected release: {release}."]
    if pieces and pieces != "TBA":
        parts.append(f"{pieces} pieces.")
    if price and price != "TBA":
        parts.append(f"Rumored price: {price}.")
    if notes:
        parts.append(notes)
    return " ".join(parts)


_ROW_FORMATTERS = {
    "brick_tap_retirement_dates.txt": _row_to_prose_retirement,
    "brick_tap_ideas.txt": _row_to_prose_ideas,
}


def _chunk_retirement_by_date(text: str, source: str) -> list[Chunk]:
    """
    Group retirement date rows by retirement date, one chunk per date.
    This makes queries like "which sets retire July 31, 2026?" retrieve a
    single chunk listing every set for that date rather than competing against
    25 individual-row chunks that all look structurally identical to the model.
    """
    lines = text.splitlines()
    col_names: list[str] = []
    data_start = 0
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.split("\t")]
        if len([c for c in cells if c]) >= 3:
            col_names = cells
            data_start = i + 1
            break

    # Group rows by retirement date, preserving insertion order
    from collections import defaultdict
    groups: dict[str, list[str]] = defaultdict(list)

    for line in lines[data_start:]:
        stripped = line.strip()
        if not stripped:
            continue
        cells = [c.strip() for c in stripped.split("\t")]
        if len([c for c in cells if c]) < 2:
            continue
        row_dict = {col_names[i]: cells[i] for i in range(min(len(col_names), len(cells)))}

        retire_date = _expand_date(row_dict.get("Retirement Date", "").strip())
        if not retire_date:
            continue

        set_num = row_dict.get("Set #", "").strip()
        name    = row_dict.get("Set Name", "").strip()
        pieces  = row_dict.get("Piece Count", "").strip()
        notes   = row_dict.get("Notes: (Exclusivity, release, etc.)", "").strip()

        entry = f"set {set_num} {name}"
        if pieces:
            entry += f" ({pieces} pieces)"
        if notes:
            entry += f" — {notes}"
        groups[retire_date].append(entry)

    chunks: list[Chunk] = []
    for date, entries in groups.items():
        count = len(entries)
        set_list = "; ".join(entries)
        text_block = (
            f"LEGO Ideas sets retiring {date} ({count} set{'s' if count != 1 else ''}): "
            f"{set_list}."
        )
        chunks.append(Chunk(text_block, source, len(chunks), "fixed-size"))

    return chunks


def chunk_structured(text: str, source: str) -> list[Chunk]:
    # Retirement dates file: group by date so one chunk covers all sets per date
    if source == "brick_tap_retirement_dates.txt":
        return _chunk_retirement_by_date(text, source)

    lines = text.splitlines()

    # Header = first line with at least 3 non-empty tab-separated cells.
    # This skips metadata rows (e.g. the "Check out Brick Tap…" line in
    # brick_tap_ideas.txt that only has 2 non-empty cells).
    col_names: list[str] = []
    data_start = 0
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.split("\t")]
        non_empty = [c for c in cells if c]
        if len(non_empty) >= 3:
            col_names = cells  # keep all cells including empty ones (preserve column positions)
            data_start = i + 1
            break

    formatter = _ROW_FORMATTERS.get(source)

    chunks: list[Chunk] = []
    for line in lines[data_start:]:
        stripped = line.strip()
        if not stripped:
            continue
        cells = [c.strip() for c in stripped.split("\t")]
        non_empty = [c for c in cells if c]
        if len(non_empty) < 2:
            continue  # skip section-header rows like "Ideas Pipeline"

        if formatter and col_names:
            # Build a column→value dict and convert to prose
            row_dict = {col_names[i]: cells[i] for i in range(min(len(col_names), len(cells)))}
            chunk_text = formatter(row_dict)
        else:
            # Fallback: key: value pairs (still better than raw tabs)
            chunk_text = " | ".join(
                f"{col_names[i]}: {cells[i]}"
                for i in range(min(len(col_names), len(cells)))
                if col_names[i] and cells[i]
            )

        chunks.append(Chunk(chunk_text, source, len(chunks), "fixed-size"))

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
