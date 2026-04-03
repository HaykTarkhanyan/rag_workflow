"""
Basic corpus statistics for scraped Infocom.am articles.
Helps inform chunking and embedding decisions.

Usage:
    python corpus_stats.py
"""

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_FILE = Path("scraped_data/infocom_investigations.json")


def word_count(text: str) -> int:
    return len(text.split())


def sentence_count(text: str) -> int:
    # Armenian sentences end with ։ (Armenian full stop) or standard . ! ?
    return len(re.split(r'[։.!?]+', text.strip())) - 1 or 1


def paragraph_count(text: str) -> int:
    return len([p for p in text.split("\n\n") if p.strip()])


def char_count_no_spaces(text: str) -> int:
    return len(text.replace(" ", "").replace("\n", ""))


def percentile(sorted_vals: list, p: float):
    idx = int(len(sorted_vals) * p / 100)
    return sorted_vals[min(idx, len(sorted_vals) - 1)]


def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    articles = [a for a in data["articles"] if a.get("content")]

    print(f"Corpus: {data['source']} / {data['category']}")
    print(f"Scraped: {data['scraped_at']}")
    print(f"Articles: {len(articles)}")
    print()

    # Collect per-article stats
    stats = []
    all_words = []
    for a in articles:
        content = a["content"]
        words = word_count(content)
        chars = len(content)
        chars_no_sp = char_count_no_spaces(content)
        sents = sentence_count(content)
        paras = paragraph_count(content)
        avg_word_len = chars_no_sp / max(words, 1)
        stats.append({
            "title": a.get("title", "?")[:60],
            "words": words,
            "chars": chars,
            "chars_no_spaces": chars_no_sp,
            "sentences": sents,
            "paragraphs": paras,
            "avg_word_len": avg_word_len,
        })
        all_words.extend(content.split())

    # Overall corpus stats
    total_words = sum(s["words"] for s in stats)
    total_chars = sum(s["chars"] for s in stats)
    total_sents = sum(s["sentences"] for s in stats)
    total_paras = sum(s["paragraphs"] for s in stats)

    print("=" * 60)
    print("CORPUS TOTALS")
    print("=" * 60)
    print(f"  Total words:       {total_words:,}")
    print(f"  Total characters:  {total_chars:,}")
    print(f"  Total sentences:   {total_sents:,}")
    print(f"  Total paragraphs:  {total_paras:,}")
    print()

    # Per-article distribution
    word_counts = sorted(s["words"] for s in stats)
    char_counts = sorted(s["chars"] for s in stats)
    sent_counts = sorted(s["sentences"] for s in stats)
    para_counts = sorted(s["paragraphs"] for s in stats)

    print("=" * 60)
    print("PER-ARTICLE DISTRIBUTION")
    print("=" * 60)
    for label, vals in [
        ("Words", word_counts),
        ("Characters", char_counts),
        ("Sentences", sent_counts),
        ("Paragraphs", para_counts),
    ]:
        print(f"\n  {label}:")
        print(f"    Min:    {vals[0]:,}")
        print(f"    P25:    {percentile(vals, 25):,}")
        print(f"    Median: {percentile(vals, 50):,}")
        print(f"    P75:    {percentile(vals, 75):,}")
        print(f"    Max:    {vals[-1]:,}")
        print(f"    Mean:   {sum(vals) // len(vals):,}")

    # Average sentence and paragraph lengths
    avg_words_per_sent = total_words / max(total_sents, 1)
    avg_words_per_para = total_words / max(total_paras, 1)
    avg_sents_per_article = total_sents / len(stats)

    print()
    print("=" * 60)
    print("AVERAGES (useful for chunking)")
    print("=" * 60)
    print(f"  Avg words/sentence:   {avg_words_per_sent:.1f}")
    print(f"  Avg words/paragraph:  {avg_words_per_para:.1f}")
    print(f"  Avg sentences/article: {avg_sents_per_article:.1f}")
    print(f"  Avg chars/word:       {sum(s['avg_word_len'] for s in stats) / len(stats):.1f}")

    # Token estimation (rough: Armenian ~1.5-2 tokens per word for most models)
    print()
    print("=" * 60)
    print("TOKEN ESTIMATES (for embedding models)")
    print("=" * 60)
    print(f"  ~1.5 tokens/word (Armenian):  {int(total_words * 1.5):,} tokens total")
    print(f"  Per article median:           ~{int(percentile(word_counts, 50) * 1.5):,} tokens")
    print(f"  Per article max:              ~{int(word_counts[-1] * 1.5):,} tokens")
    print()
    print("  Metric-AI embeddings max input: 512 tokens")
    print(f"  Articles fitting in 512 tokens: {sum(1 for w in word_counts if w * 1.5 <= 512)}/{len(word_counts)}")
    print(f"  -> Most articles need chunking for embedding")

    # Shortest and longest articles
    by_words = sorted(stats, key=lambda s: s["words"])
    print()
    print("=" * 60)
    print("SHORTEST 5 ARTICLES")
    print("=" * 60)
    for s in by_words[:5]:
        print(f"  {s['words']:5,} words | {s['sentences']:3} sents | {s['title']}")

    print()
    print("=" * 60)
    print("LONGEST 5 ARTICLES")
    print("=" * 60)
    for s in by_words[-5:]:
        print(f"  {s['words']:5,} words | {s['sentences']:3} sents | {s['title']}")

    # Metadata coverage
    print()
    print("=" * 60)
    print("METADATA COVERAGE")
    print("=" * 60)
    fields = ["title", "author", "published_at", "sections", "keywords", "description", "image_url", "language"]
    for field in fields:
        count = sum(1 for a in articles if a.get(field))
        print(f"  {field:15s}: {count}/{len(articles)} ({count * 100 // len(articles)}%)")

    # Author distribution
    authors = {}
    for a in articles:
        author = a.get("author", "Unknown")
        authors[author] = authors.get(author, 0) + 1
    print()
    print("=" * 60)
    print("ARTICLES BY AUTHOR")
    print("=" * 60)
    for author, count in sorted(authors.items(), key=lambda x: -x[1]):
        print(f"  {count:3d} | {author}")

    # Date range
    dates = sorted(a["published_at"][:10] for a in articles if a.get("published_at"))
    if dates:
        print()
        print("=" * 60)
        print("DATE RANGE")
        print("=" * 60)
        print(f"  Earliest: {dates[0]}")
        print(f"  Latest:   {dates[-1]}")
        # Articles per year
        years = {}
        for d in dates:
            y = d[:4]
            years[y] = years.get(y, 0) + 1
        for y in sorted(years):
            print(f"  {y}: {years[y]} articles")


if __name__ == "__main__":
    main()
