"""
Embed chunks with Metric-AI Armenian embeddings and index into ChromaDB.

Loads chunks from chunks_sentence.json or chunks_paragraph.json,
embeds with Metric-AI/armenian-text-embeddings-2-large (1024d),
and stores in a persistent ChromaDB collection.

Usage:
    python embed_and_index.py                          # sentence chunks (default)
    python embed_and_index.py --strategy paragraph     # paragraph chunks
    python embed_and_index.py --strategy sentence --reset  # rebuild from scratch
    python embed_and_index.py --query "search text"    # test a query

Output:
    scraped_data/chroma_db/   (persistent ChromaDB storage)
"""

import argparse
import json
import sys
import time
from pathlib import Path

import chromadb
import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MODEL_NAME = "Metric-AI/armenian-text-embeddings-2-large"
EMBEDDING_DIM = 1024
BATCH_SIZE = 16  # CPU-friendly batch size

CHUNKS_DIR = Path("scraped_data")
CHROMA_DIR = Path("scraped_data/chroma_db")


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


def embed_texts(texts: list[str], tokenizer, model) -> list[list[float]]:
    """Embed a list of texts in batches. Returns list of 1024d vectors."""
    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i : i + BATCH_SIZE]
        batch_dict = tokenizer(
            batch_texts, max_length=512, padding=True, truncation=True, return_tensors="pt"
        )
        with torch.no_grad():
            outputs = model(**batch_dict)
        embeddings = average_pool(outputs.last_hidden_state, batch_dict["attention_mask"])
        embeddings = F.normalize(embeddings, p=2, dim=1)
        all_embeddings.extend(embeddings.tolist())

    return all_embeddings


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
        metadata={"hnsw:space": "cosine", "embedding_dim": EMBEDDING_DIM},
    )
    return collection


def index_chunks(strategy: str, reset: bool = False):
    """Load chunks, embed them, and index into ChromaDB."""
    chunks_file = CHUNKS_DIR / f"chunks_{strategy}.json"
    if not chunks_file.exists():
        print(f"ERROR: {chunks_file} not found. Run chunk_articles.py --strategy {strategy} first.")
        sys.exit(1)

    data = json.loads(chunks_file.read_text(encoding="utf-8"))
    chunks = data["chunks"]
    print(f"Loaded {len(chunks)} chunks ({strategy} strategy)")

    collection = get_collection(strategy, reset=reset)
    existing_count = collection.count()

    if existing_count > 0 and not reset:
        print(f"Collection already has {existing_count} items. Use --reset to rebuild.")
        print("Skipping embedding. Use --query to search.")
        return collection

    tokenizer, model = load_model()

    # Embed in batches with progress
    texts_for_embedding = [c["text_for_embedding"] for c in chunks]
    print(f"\nEmbedding {len(texts_for_embedding)} chunks (batch_size={BATCH_SIZE})...")

    all_embeddings = []
    t0 = time.time()
    for i in range(0, len(texts_for_embedding), BATCH_SIZE):
        batch_texts = texts_for_embedding[i : i + BATCH_SIZE]
        batch_embeddings = embed_texts(batch_texts, tokenizer, model)
        all_embeddings.extend(batch_embeddings)

        done = min(i + BATCH_SIZE, len(texts_for_embedding))
        elapsed = time.time() - t0
        rate = done / elapsed
        eta = (len(texts_for_embedding) - done) / rate if rate > 0 else 0
        print(f"  [{done}/{len(texts_for_embedding)}] {elapsed:.0f}s elapsed, ~{eta:.0f}s remaining")

    total_time = time.time() - t0
    print(f"\nEmbedding complete: {total_time:.1f}s ({total_time / len(chunks) * 1000:.0f}ms/chunk)")

    # Index into ChromaDB
    print(f"\nIndexing into ChromaDB...")
    # ChromaDB has a batch limit, add in chunks of 500
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

    print(f"Indexed {collection.count()} chunks into collection '{collection.name}'")
    return collection


def query_collection(strategy: str, query_text: str, n_results: int = 5):
    """Search the ChromaDB collection with a query."""
    collection = get_collection(strategy)
    if collection.count() == 0:
        print("Collection is empty. Run without --query first to index chunks.")
        return

    tokenizer, model = load_model()

    # Embed query (with "query: " prefix as per model docs)
    query_with_prefix = f"query: {query_text}"
    query_embedding = embed_texts([query_with_prefix], tokenizer, model)[0]

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
        score = 1 - dist  # cosine distance -> similarity
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
    parser.add_argument("--query", type=str, help="Search query to test retrieval")
    parser.add_argument("-n", type=int, default=5, help="Number of results for query (default: 5)")
    args = parser.parse_args()

    if args.query:
        query_collection(args.strategy, args.query, n_results=args.n)
    else:
        index_chunks(args.strategy, reset=args.reset)


if __name__ == "__main__":
    main()
