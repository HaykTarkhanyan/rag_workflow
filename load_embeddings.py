"""
Load pre-computed embeddings (from Colab) into ChromaDB.

Usage:
    python load_embeddings.py --strategy paragraph
    python load_embeddings.py --strategy sentence

Expects in scraped_data/:
    embeddings_paragraph.npy          (numpy array, shape [N, 1024])
    embeddings_paragraph_meta.json    (chunk metadata)
"""

import argparse
import json
import sys
from pathlib import Path

import chromadb
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = Path("scraped_data")
CHROMA_DIR = DATA_DIR / "chroma_db"


def load_and_index(strategy: str, reset: bool = False):
    npy_file = DATA_DIR / f"embeddings_{strategy}.npy"
    meta_file = DATA_DIR / f"embeddings_{strategy}_meta.json"

    if not npy_file.exists() or not meta_file.exists():
        print(f"ERROR: Missing {npy_file} or {meta_file}")
        print("Run the Colab notebook first, then place downloaded files in scraped_data/")
        sys.exit(1)

    embeddings = np.load(npy_file)
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    chunks = meta["chunks"]

    print(f"Loaded {len(chunks)} chunks, embeddings shape: {embeddings.shape}")

    if len(chunks) != embeddings.shape[0]:
        print(f"ERROR: Mismatch! {len(chunks)} chunks but {embeddings.shape[0]} embeddings")
        sys.exit(1)

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

    if collection.count() >= len(chunks) and not reset:
        print(f"Collection already has {collection.count()} items. Use --reset to rebuild.")
        return

    for i in range(0, len(chunks), 500):
        batch = chunks[i : i + 500]
        batch_emb = embeddings[i : i + 500].tolist()

        collection.add(
            ids=[c["chunk_id"] for c in batch],
            embeddings=batch_emb,
            documents=[c["text"] for c in batch],
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
                for c in batch
            ],
        )

    print(f"Indexed {collection.count()} chunks into '{collection_name}'")


def main():
    parser = argparse.ArgumentParser(description="Load Colab embeddings into ChromaDB")
    parser.add_argument("--strategy", choices=["sentence", "paragraph"], required=True)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    load_and_index(args.strategy, reset=args.reset)


if __name__ == "__main__":
    main()
