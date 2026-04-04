"""
Chunk scraped Infocom.am articles for embedding with Metric-AI models.

Strategy: Sentence-group chunking targeting ~100-120 tokens to match
the model's 128-token training window (512-token hard limit).

NOTE: We should also try paragraph-group chunking (~300-400 tokens)
      to compare retrieval quality. The model accepts up to 512 tokens
      at inference even though it was trained on 128. Larger chunks
      carry more context. Run with --strategy paragraph to test this.

Usage:
    python chunk_articles.py                     # sentence-group (default)
    python chunk_articles.py --strategy paragraph  # paragraph-group
    python chunk_articles.py --stats             # just print chunk stats

Output:
    scraped_data/chunks_sentence.json
    scraped_data/chunks_paragraph.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_FILE = Path("scraped_data/infocom_investigations.json")
OUTPUT_DIR = Path("scraped_data")

# -- Chunking parameters --
# Sentence strategy: targets model's 128-token training window
SENTENCE_TARGET_TOKENS = 110
SENTENCE_MAX_TOKENS = 140
SENTENCE_OVERLAP_SENTS = 1

# Paragraph strategy: uses more of the 512-token inference window
PARAGRAPH_TARGET_TOKENS = 350
PARAGRAPH_MAX_TOKENS = 450
PARAGRAPH_OVERLAP_PARAS = 1

# Armenian has ~1.5 tokens/word on average (measured with XLM-RoBERTa tokenizer)
TOKENS_PER_WORD = 1.5


def estimate_tokens(text: str) -> int:
    """Estimate token count. Armenian averages ~1.5 tokens/word."""
    return int(len(text.split()) * TOKENS_PER_WORD)


def split_sentences(text: str) -> list[str]:
    """Split text into sentences using Armenian and standard punctuation."""
    # Split on Armenian full stop (։), period, !, ? followed by space or end
    parts = re.split(r'(?<=[։.!?])\s+', text)
    return [s.strip() for s in parts if s.strip()]


def split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs on double newlines."""
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def chunk_by_units(
    units: list[str],
    target_tokens: int,
    max_tokens: int,
    overlap: int,
    separator: str = " ",
) -> list[dict]:
    """Group text units (sentences or paragraphs) into chunks.

    Returns list of {text, unit_start, unit_end, token_estimate}.
    """
    chunks = []
    i = 0
    while i < len(units):
        chunk_units = []
        chunk_tokens = 0

        j = i
        while j < len(units):
            unit_tokens = estimate_tokens(units[j])
            if chunk_tokens + unit_tokens > max_tokens and chunk_units:
                break
            chunk_units.append(units[j])
            chunk_tokens += unit_tokens
            if chunk_tokens >= target_tokens:
                j += 1
                break
            j += 1

        chunk_text = separator.join(chunk_units)
        chunks.append({
            "text": chunk_text,
            "unit_start": i,
            "unit_end": j,
            "token_estimate": estimate_tokens(chunk_text),
        })

        # Advance with overlap
        i = max(j - overlap, i + 1)

    return chunks


def make_article_id(article: dict, index: int) -> str:
    """Generate a stable article ID from URL."""
    match = re.search(r"infocom\.am/(\d+)/", article.get("url", ""))
    return f"infocom_{match.group(1)}" if match else f"infocom_{index:04d}"


def build_chunk_metadata(article: dict, article_id: str) -> dict:
    """Extract metadata to attach to each chunk."""
    return {
        "article_id": article_id,
        "title": article.get("title", ""),
        "author": article.get("author", ""),
        "published_at": article.get("published_at", ""),
        "sections": article.get("sections", []),
        "url": article.get("url", ""),
        "language": article.get("language", "hy-AM"),
    }


def chunk_article(article: dict, article_id: str, strategy: str) -> list[dict]:
    """Chunk a single article. Returns list of chunk dicts."""
    content = article.get("content", "")
    if not content:
        return []

    metadata = build_chunk_metadata(article, article_id)

    if strategy == "sentence":
        units = split_sentences(content)
        sep = " "
        raw_chunks = chunk_by_units(units, SENTENCE_TARGET_TOKENS, SENTENCE_MAX_TOKENS, SENTENCE_OVERLAP_SENTS, separator=sep)
    else:  # paragraph
        units = split_paragraphs(content)
        sep = "\n\n"
        raw_chunks = chunk_by_units(units, PARAGRAPH_TARGET_TOKENS, PARAGRAPH_MAX_TOKENS, PARAGRAPH_OVERLAP_PARAS, separator=sep)

    # Filter out tiny trailing chunks -- merge into previous if possible
    MIN_TOKENS = 20
    if len(raw_chunks) > 1 and raw_chunks[-1]["token_estimate"] < MIN_TOKENS:
        last = raw_chunks.pop()
        raw_chunks[-1]["text"] += sep + last["text"]
        raw_chunks[-1]["token_estimate"] = estimate_tokens(raw_chunks[-1]["text"])

    chunks = []
    for i, rc in enumerate(raw_chunks):
        # Short metadata prefix for embedding context
        prefix = f"{metadata['title']}"
        chunk_text_for_embedding = f"passage: {prefix}. {rc['text']}"
        # Token estimate includes the prefix that actually gets sent to the model
        embedding_token_estimate = estimate_tokens(chunk_text_for_embedding)

        chunks.append({
            "chunk_id": f"{article_id}_chunk_{i:03d}",
            "article_id": article_id,
            "chunk_index": i,
            "total_chunks": len(raw_chunks),
            "text": rc["text"],
            "text_for_embedding": chunk_text_for_embedding,
            "token_estimate": rc["token_estimate"],
            "embedding_token_estimate": embedding_token_estimate,
            "metadata": metadata,
        })

    return chunks


def main():
    parser = argparse.ArgumentParser(description="Chunk articles for embedding")
    parser.add_argument("--strategy", choices=["sentence", "paragraph"], default="sentence",
                        help="Chunking strategy (default: sentence)")
    parser.add_argument("--stats", action="store_true", help="Print stats only, don't save")
    args = parser.parse_args()

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    articles = [a for a in data["articles"] if a.get("content")]

    print(f"Strategy: {args.strategy}")
    print(f"Articles: {len(articles)}")
    print()

    all_chunks = []
    for idx, article in enumerate(articles):
        article_id = make_article_id(article, idx)
        chunks = chunk_article(article, article_id, args.strategy)
        all_chunks.extend(chunks)

    # Stats
    token_counts = [c["token_estimate"] for c in all_chunks]
    token_counts.sort()

    print("=" * 60)
    print(f"CHUNK STATS ({args.strategy} strategy)")
    print("=" * 60)
    print(f"  Total chunks:     {len(all_chunks)}")
    print(f"  Total articles:   {len(articles)}")
    print(f"  Avg chunks/article: {len(all_chunks) / len(articles):.1f}")
    print()
    print(f"  Token estimates per chunk:")
    print(f"    Min:    {token_counts[0]}")
    print(f"    P25:    {token_counts[len(token_counts) // 4]}")
    print(f"    Median: {token_counts[len(token_counts) // 2]}")
    print(f"    P75:    {token_counts[3 * len(token_counts) // 4]}")
    print(f"    Max:    {token_counts[-1]}")
    print(f"    Mean:   {sum(token_counts) // len(token_counts)}")
    print()

    # Chunks that exceed 512 tokens
    over_512 = sum(1 for t in token_counts if t > 512)
    over_128 = sum(1 for t in token_counts if t > 128)
    print(f"  Over 128 tokens:  {over_128}/{len(all_chunks)}")
    print(f"  Over 512 tokens:  {over_512}/{len(all_chunks)}")

    if args.stats:
        return

    # Save chunks
    output_file = OUTPUT_DIR / f"chunks_{args.strategy}.json"
    output = {
        "source": data["source"],
        "category": data["category"],
        "strategy": args.strategy,
        "parameters": {
            "sentence": {
                "target_tokens": SENTENCE_TARGET_TOKENS,
                "max_tokens": SENTENCE_MAX_TOKENS,
                "overlap_units": SENTENCE_OVERLAP_SENTS,
            },
            "paragraph": {
                "target_tokens": PARAGRAPH_TARGET_TOKENS,
                "max_tokens": PARAGRAPH_MAX_TOKENS,
                "overlap_units": PARAGRAPH_OVERLAP_PARAS,
            },
        }[args.strategy],
        "tokens_per_word_estimate": TOKENS_PER_WORD,
        "total_chunks": len(all_chunks),
        "total_articles": len(articles),
        "chunks": all_chunks,
    }

    output_file.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved {len(all_chunks)} chunks to {output_file}")


if __name__ == "__main__":
    main()
