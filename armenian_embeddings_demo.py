"""
Demo: Metric-AI Armenian Text Embeddings 2
Models: https://huggingface.co/Metric-AI/armenian-text-embeddings-2-base
        https://huggingface.co/Metric-AI/armenian-text-embeddings-2-large

Install:
    uv pip install transformers torch sentence-transformers
"""

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel


MODEL_NAME = "Metric-AI/armenian-text-embeddings-2-base"
# For higher quality (but slower): "Metric-AI/armenian-text-embeddings-2-large"


def average_pool(last_hidden_states: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


def get_embeddings(texts: list[str], tokenizer, model) -> torch.Tensor:
    batch_dict = tokenizer(texts, max_length=512, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**batch_dict)
    embeddings = average_pool(outputs.last_hidden_state, batch_dict["attention_mask"])
    return F.normalize(embeddings, p=2, dim=1)


def main():
    print(f"Loading model: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
    model.eval()

    # --- Semantic similarity between queries and passages ---
    # Prefix queries with "query: " and documents with "passage: "
    queries = [
        "query: Ինչպես պատրաստել տոլմա",
        "query: Քանի գրամ սպիտակուց է հարկավոր օրական",
    ]

    passages = [
        (
            "passage: Տոլմայի բաղադրատոմս. "
            "Բաղադրիչներ՝ 500գ աղացած միս, 1 բաժակ բրինձ, "
            "Խաղողի տերևներ, 2 գլուխ սոխ, "
            "Համեմունքներ՝ աղ, սև պղպեղ, քարի"
        ),
        (
            "passage: Սպիտակուցի օրական չափաբաժինը կախված է մարդու քաշից, "
            "սեռից և ֆիզիկական ակտիվությունից: "
            "Միջին հաշվով, կանանց համար խորհուրդ է տրվում "
            "46-50 գրամ սպիտակուց օրական:"
        ),
    ]

    all_texts = queries + passages
    embeddings = get_embeddings(all_texts, tokenizer, model)

    query_embs = embeddings[: len(queries)]
    passage_embs = embeddings[len(queries) :]

    scores = (query_embs @ passage_embs.T) * 100
    print("\n--- Similarity Scores (queries x passages) ---")
    for i, q in enumerate(queries):
        for j, p in enumerate(passages):
            print(f"  Q{i} vs P{j}: {scores[i][j].item():.2f}")

    # --- Using SentenceTransformers (simpler API) ---
    print("\n--- SentenceTransformers API ---")
    try:
        from sentence_transformers import SentenceTransformer

        st_model = SentenceTransformer(MODEL_NAME)
        st_embeddings = st_model.encode(all_texts, normalize_embeddings=True)
        print(f"  Embedding shape: {st_embeddings.shape}")
        print(f"  Embedding dim: {st_embeddings.shape[1]}")
    except ImportError:
        print("  sentence-transformers not installed, skipping.")
        print("  Install with: uv pip install sentence-transformers")

    print("\nDone!")


if __name__ == "__main__":
    main()
