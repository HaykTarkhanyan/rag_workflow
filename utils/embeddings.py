"""Shared embedding utilities for Metric-AI Armenian models."""

import time

import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer

MODEL_NAME = "Metric-AI/armenian-text-embeddings-2-large"
EMBEDDING_DIM = 1024
DEFAULT_BATCH_SIZE = 8


def average_pool(last_hidden_states: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


def load_model(model_name: str = MODEL_NAME):
    """Load tokenizer and model. Returns (tokenizer, model)."""
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()
    print(f"Model loaded in {time.time() - t0:.1f}s", flush=True)
    return tokenizer, model


def embed_batch(texts: list[str], tokenizer, model) -> list[list[float]]:
    """Embed a single batch of texts. Returns list of vectors."""
    batch_dict = tokenizer(
        texts, max_length=512, padding=True, truncation=True, return_tensors="pt"
    )
    with torch.no_grad():
        outputs = model(**batch_dict)
    embeddings = average_pool(outputs.last_hidden_state, batch_dict["attention_mask"])
    embeddings = F.normalize(embeddings, p=2, dim=1)
    return embeddings.tolist()


def embed_texts(texts: list[str], tokenizer, model, batch_size: int = DEFAULT_BATCH_SIZE) -> list[list[float]]:
    """Embed texts in batches. Returns list of vectors."""
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        all_embeddings.extend(embed_batch(batch, tokenizer, model))
    return all_embeddings


def build_chroma_metadata(chunk: dict, strategy: str) -> dict:
    """Build a flat metadata dict for ChromaDB from a chunk."""
    return {
        "article_id": chunk["metadata"]["article_id"],
        "title": chunk["metadata"]["title"],
        "author": chunk["metadata"]["author"],
        "published_at": chunk["metadata"]["published_at"],
        "url": chunk["metadata"]["url"],
        "chunk_index": chunk["chunk_index"],
        "total_chunks": chunk["total_chunks"],
        "strategy": strategy,
    }
