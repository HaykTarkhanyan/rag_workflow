"""
Embed chunks with Metric-AI Armenian embeddings and index into ChromaDB.

Features:
- Caches embeddings to disk (scraped_data/embeddings_cache/) to avoid recomputation
- Supports --limit N to embed only first N chunks for testing
- Supports --query to test retrieval

Usage:
    python embed_and_index.py --strategy paragraph --limit 20   # test with 20 chunks
    python embed_and_index.py --strategy paragraph              # embed all (uses cache)
    python embed_and_index.py --strategy paragraph --reset      # rebuild from scratch
    python embed_and_index.py --strategy paragraph --query "search text"

Output:
    scraped_data/chroma_db/           (persistent ChromaDB storage)
    scraped_data/embeddings_cache/    (cached embedding vectors)
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import chromadb
import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import functools
print = functools.partial(print, flush=True)

MODEL_NAME = "Metric-AI/armenian-text-embeddings-2-large"
EMBEDDING_DIM = 1024
BATCH_SIZE = 8  # smaller batch = less memory, more frequent progress

CHUNKS_DIR = Path("scraped_data")
CHROMA_DIR = Path("scraped_data/chroma_db")
CACHE_DIR = Path("scraped_data/embeddings_cache")


def average_pool(last_hidden_states: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


def load_model():
    """Load tokenizer and model."""
    print(f"Loading model: {MODEL_NAME}")
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
    model.eval()
    print(f"Model loaded in {time.time() - t0:.1f}s")
    return tokenizer, model


def cache_key(text: str) -> str:
    """Generate a short hash for caching an embedding."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def get_cached_embedding(text: str) -> list[float] | None:
    """Load cached embedding if it exists."""
    path = CACHE_DIR / f"{cache_key(text)}.npy"
    if path.exists():
        return np.load(path).tolist()
    return None


def save_cached_embedding(text: str, embedding: list[float]):
    """Save embedding to cache."""
    path = CACHE_DIR / f"{cache_key(text)}.npy"
    np.save(path, np.array(embedding, dtype=np.float32))


def embed_batch(texts: list[str], tokenizer, model) -> list[list[float]]:
    """Embed a single batch of texts."""
    batch_dict = tokenizer(
        texts, max_length=512, padding=True, truncation=True, return_tensors="pt"
    )
    with torch.no_grad():
        outputs = model(**batch_dict)
    embeddings = average_pool(outputs.last_hidden_state, batch_dict["attention_mask"])
    embeddings = F.normalize(embeddings, p=2, dim=1)
    return embeddings.tolist()


def embed_texts_with_cache(texts: list[str], tokenizer, model) -> list[list[float]]:
    """Embed texts, using cache where available. Returns list of 1024d vectors."""
    results = [None] * len(texts)
    to_embed_indices = []
    to_embed_texts = []
    cached_count = 0

    # Check cache first
    for i, text in enumerate(texts):
        cached = get_cached_embedding(text)
        if cached is not None:
            results[i] = cached
            cached_count += 1
        else:
            to_embed_indices.append(i)
            to_embed_texts.append(text)

    if cached_count > 0:
        print(f"  {cached_count} embeddings loaded from cache, {len(to_embed_texts)} to compute")

    if not to_embed_texts:
        return results

    # Embed uncached texts in batches
    t0 = time.time()
    for batch_start in range(0, len(to_embed_texts), BATCH_SIZE):
        batch = to_embed_texts[batch_start : batch_start + BATCH_SIZE]
        batch_embeddings = embed_batch(batch, tokenizer, model)

        for j, emb in enumerate(batch_embeddings):
            idx = to_embed_indices[batch_start + j]
            results[idx] = emb
            save_cached_embedding(texts[idx], emb)

        done = min(batch_start + BATCH_SIZE, len(to_embed_texts))
        elapsed = time.time() - t0
        rate = done / elapsed if elapsed > 0 else 0
        eta = (len(to_embed_texts) - done) / rate if rate > 0 else 0
        print(f"  Embedded [{done}/{len(to_embed_texts)}] {elapsed:.0f}s elapsed, ~{eta:.0f}s remaining")

    total = time.time() - t0
    print(f"  Computed {len(to_embed_texts)} embeddings in {total:.1f}s ({total/len(to_embed_texts)*1000:.0f}ms/chunk)")

    return results


def get_collection(strategy: str, reset: bool = False) -> chromadb.Collection:
    """Get or create a ChromaDB collection."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection_name = f"infocom_investigations_{strategy}"

    if reset:
        try:
            client.delete_collection(collection_name)
            print(f"Deleted existing collection: {collection_name}")
        except ValueError:
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def index_chunks(strategy: str, reset: bool = False, limit: int | None = None):
    """Load chunks, embed them, and index into ChromaDB."""
    chunks_file = CHUNKS_DIR / f"chunks_{strategy}.json"
    if not chunks_file.exists():
        print(f"ERROR: {chunks_file} not found. Run chunk_articles.py --strategy {strategy} first.")
        sys.exit(1)

    data = json.loads(chunks_file.read_text(encoding="utf-8"))
    chunks = data["chunks"]

    if limit:
        chunks = chunks[:limit]
        print(f"Limited to first {limit} chunks (of {data['total_chunks']} total)")

    print(f"Processing {len(chunks)} chunks ({strategy} strategy)")

    collection = get_collection(strategy, reset=reset)
    existing_count = collection.count()

    if existing_count >= len(chunks) and not reset:
        print(f"Collection already has {existing_count} items. Use --reset to rebuild.")
        return collection

    tokenizer, model = load_model()

    # Embed with caching
    texts_for_embedding = [c["text_for_embedding"] for c in chunks]
    print(f"\nEmbedding {len(texts_for_embedding)} chunks...")
    all_embeddings = embed_texts_with_cache(texts_for_embedding, tokenizer, model)

    # Index into ChromaDB
    print(f"\nIndexing into ChromaDB...")
    if reset or existing_count == 0:
        for i in range(0, len(chunks), 500):
            batch_chunks = chunks[i : i + 500]
            batch_embeddings = all_embeddings[i : i + 500]

            collection.add(
                ids=[c["chunk_id"] for c in batch_chunks],
                embeddings=batch_embeddings,
                documents=[c["text"] for c in batch_chunks],
                metadatas=[
                    {
                        "article_id": c["metadata"]["article_id"],
                        "title": c["metadata"]["title"],
                        "author": c["metadata"]["author"],
                        "published_at": c["metadata"]["published_at"],
                        "url": c["metadata"]["url"],
                        "chunk_index": c["chunk_index"],
                        "total_chunks": c["total_chunks"],
                        "strategy": strategy,
                    }
                    for c in batch_chunks
                ],
            )

    print(f"Indexed {collection.count()} chunks into '{collection.name}'")
    return collection


def query_collection(strategy: str, query_text: str, n_results: int = 5):
    """Search the ChromaDB collection with a query."""
    collection = get_collection(strategy)
    if collection.count() == 0:
        print("Collection is empty. Run without --query first to index chunks.")
        return

    tokenizer, model = load_model()

    query_with_prefix = f"query: {query_text}"
    query_embedding = embed_batch([query_with_prefix], tokenizer, model)[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    print(f"\nQuery: {query_text}")
    print(f"Strategy: {strategy}")
    print(f"Results: {len(results['ids'][0])}")
    print("=" * 60)

    for i, (doc, meta, dist) in enumerate(
        zip(results["documents"][0], results["metadatas"][0], results["distances"][0])
    ):
        score = 1 - dist
        print(f"\n--- Result {i + 1} (similarity: {score:.4f}) ---")
        print(f"Article: {meta['title'][:70]}")
        print(f"Author:  {meta['author']} | Date: {meta['published_at'][:10]}")
        print(f"Chunk:   {meta['chunk_index'] + 1}/{meta['total_chunks']}")
        print(f"URL:     {meta['url']}")
        print(f"Text:    {doc[:200]}...")


def main():
    parser = argparse.ArgumentParser(description="Embed and index chunks into ChromaDB")
    parser.add_argument("--strategy", choices=["sentence", "paragraph"], default="sentence")
    parser.add_argument("--reset", action="store_true", help="Delete and rebuild the collection")
    parser.add_argument("--limit", type=int, help="Only process first N chunks (for testing)")
    parser.add_argument("--query", type=str, help="Search query to test retrieval")
    parser.add_argument("-n", type=int, default=5, help="Number of results for query (default: 5)")
    args = parser.parse_args()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if args.query:
        query_collection(args.strategy, args.query, n_results=args.n)
    else:
        index_chunks(args.strategy, reset=args.reset, limit=args.limit)


if __name__ == "__main__":
    main()
