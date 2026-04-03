"""
Evaluate RAG retrieval quality on both chunking strategies.

Embeds test questions, queries both ChromaDB collections,
compares against expected chunk_ids, and reports metrics.
Optionally uses Gemini to judge answer quality.

Usage:
    python evaluate_retrieval.py                    # full evaluation
    python evaluate_retrieval.py --k 3 5 10         # custom k values
    python evaluate_retrieval.py --gemini            # include Gemini answer judging

Output:
    Prints comparison table + saves results to test_data/eval_results.json
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import chromadb
import numpy as np
import torch
import torch.nn.functional as F
from dotenv import load_dotenv
from transformers import AutoModel, AutoTokenizer

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import functools
print = functools.partial(print, flush=True)

load_dotenv()

# Logging setup
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "evaluate_retrieval.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("evaluate")

# Gemini pricing (per 1M tokens, as of 2026-04)
GEMINI_PRICING = {
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},  # $/1M tokens
}

MODEL_NAME = "Metric-AI/armenian-text-embeddings-2-large"
CHROMA_DIR = Path("scraped_data/chroma_db")
QA_FILE = Path("test_data/qa_pairs.json")
RESULTS_FILE = Path("test_data/eval_results.json")


def average_pool(last_hidden_states, attention_mask):
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


def embed_texts(texts, tokenizer, model):
    """Embed texts on CPU."""
    batch = tokenizer(texts, max_length=512, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        out = model(**batch)
    emb = average_pool(out.last_hidden_state, batch["attention_mask"])
    return F.normalize(emb, p=2, dim=1).tolist()


def recall_at_k(retrieved_ids: list[str], expected_ids: list[str], k: int) -> float:
    """Fraction of expected IDs found in top-k retrieved."""
    top_k = set(retrieved_ids[:k])
    found = len(top_k & set(expected_ids))
    return found / len(expected_ids) if expected_ids else 0.0


def reciprocal_rank(retrieved_ids: list[str], expected_ids: list[str]) -> float:
    """1/rank of first expected ID found in retrieved list."""
    expected_set = set(expected_ids)
    for i, rid in enumerate(retrieved_ids):
        if rid in expected_set:
            return 1.0 / (i + 1)
    return 0.0


def precision_at_k(retrieved_ids: list[str], expected_ids: list[str], k: int) -> float:
    """Fraction of top-k that are relevant."""
    top_k = retrieved_ids[:k]
    expected_set = set(expected_ids)
    relevant = sum(1 for rid in top_k if rid in expected_set)
    return relevant / k if k > 0 else 0.0


def evaluate_strategy(strategy: str, qa_pairs: list, query_embeddings: list, k_values: list) -> dict:
    """Evaluate retrieval for one strategy."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection_name = f"infocom_investigations_{strategy}"

    try:
        collection = client.get_collection(collection_name)
    except Exception:
        print(f"  ERROR: Collection '{collection_name}' not found")
        return {}

    print(f"  Querying {collection.count()} chunks in '{collection_name}'...")

    max_k = max(k_values)
    results_per_query = []

    for i, (qa, q_emb) in enumerate(zip(qa_pairs, query_embeddings)):
        result = collection.query(
            query_embeddings=[q_emb],
            n_results=max_k,
            include=["documents", "metadatas", "distances"],
        )

        retrieved_ids = result["ids"][0]
        retrieved_docs = result["documents"][0]
        retrieved_metas = result["metadatas"][0]
        distances = result["distances"][0]
        expected = qa["expected_chunk_ids"]

        query_result = {
            "id": qa["id"],
            "question": qa["question"],
            "expected_chunk_ids": expected,
            "retrieved_ids": retrieved_ids,
            "retrieved_titles": [m["title"][:60] for m in retrieved_metas],
            "distances": distances,
        }

        for k in k_values:
            query_result[f"recall@{k}"] = recall_at_k(retrieved_ids, expected, k)
            query_result[f"precision@{k}"] = precision_at_k(retrieved_ids, expected, k)
        query_result["mrr"] = reciprocal_rank(retrieved_ids, expected)

        # Check if any expected chunk's article_id appears (looser match)
        expected_articles = set(eid.rsplit("_chunk_", 1)[0] for eid in expected)
        retrieved_articles = [rid.rsplit("_chunk_", 1)[0] for rid in retrieved_ids]
        for k in k_values:
            top_k_articles = set(retrieved_articles[:k])
            query_result[f"article_recall@{k}"] = len(top_k_articles & expected_articles) / len(expected_articles)

        results_per_query.append(query_result)

    # Aggregate metrics
    metrics = {}
    for k in k_values:
        metrics[f"recall@{k}"] = np.mean([r[f"recall@{k}"] for r in results_per_query])
        metrics[f"precision@{k}"] = np.mean([r[f"precision@{k}"] for r in results_per_query])
        metrics[f"article_recall@{k}"] = np.mean([r[f"article_recall@{k}"] for r in results_per_query])
    metrics["mrr"] = np.mean([r["mrr"] for r in results_per_query])

    # Metrics by difficulty
    for difficulty in ["easy", "medium", "hard"]:
        subset = [r for r, qa in zip(results_per_query, qa_pairs) if qa.get("difficulty") == difficulty]
        if subset:
            metrics[f"mrr_{difficulty}"] = np.mean([r["mrr"] for r in subset])
            for k in k_values:
                metrics[f"recall@{k}_{difficulty}"] = np.mean([r[f"recall@{k}"] for r in subset])

    return {"strategy": strategy, "metrics": metrics, "per_query": results_per_query}


def gemini_judge(qa_pairs, strategy_results, strategy):
    """Use Gemini to judge if retrieved chunks can answer the question."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        print("  SKIP: No GEMINI_API_KEY in .env")
        return strategy_results

    from google import genai

    client = genai.Client(api_key=api_key)

    gemini_model = "gemini-2.5-flash"
    print(f"  Judging {len(qa_pairs)} answers with {gemini_model}...")
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_collection(f"infocom_investigations_{strategy}")
    judged = 0
    total_input_tokens = 0
    total_output_tokens = 0
    for qa, result in zip(qa_pairs, strategy_results["per_query"]):
        chroma_result = collection.get(
            ids=result["retrieved_ids"][:3],
            include=["documents"],
        )
        top3_texts = chroma_result["documents"]

        prompt = f"""You are evaluating a RAG system. Given a question, the expected answer, and the top 3 retrieved text chunks, judge whether the retrieved chunks contain enough information to answer the question.

Question: {qa['question']}
Expected answer: {qa['answer']}

Retrieved chunks:
{chr(10).join(f'Chunk {i+1}: {doc[:300]}...' for i, doc in enumerate(top3_texts))}

Respond with ONLY a JSON object:
{{"answerable": true/false, "score": 0-5, "reason": "brief explanation in English"}}
- score 5: perfect answer in chunks
- score 3: partial answer
- score 0: completely wrong/unrelated chunks"""

        try:
            response = client.models.generate_content(
                model=gemini_model,
                contents=prompt,
            )
            text = response.text.strip()

            # Track token usage
            usage = response.usage_metadata
            if usage:
                total_input_tokens += getattr(usage, "prompt_token_count", 0) or 0
                total_output_tokens += getattr(usage, "candidates_token_count", 0) or 0

            # Extract JSON from response
            if "```" in text:
                text = text.split("```")[1].strip()
                if text.startswith("json"):
                    text = text[4:].strip()
            judgment = json.loads(text)
            result["gemini_judgment"] = judgment
            judged += 1
        except Exception as e:
            logger.warning(f"Gemini error for {qa['id']}: {e}")
            result["gemini_judgment"] = {"error": str(e)}

        time.sleep(0.5)  # rate limit

    # Report cost
    pricing = GEMINI_PRICING.get(gemini_model, {"input": 0, "output": 0})
    cost = (total_input_tokens * pricing["input"] + total_output_tokens * pricing["output"]) / 1_000_000
    print(f"  Judged {judged}/{len(qa_pairs)} questions")
    print(f"  Tokens: {total_input_tokens:,} input + {total_output_tokens:,} output = {total_input_tokens + total_output_tokens:,} total")
    print(f"  Estimated cost: ${cost:.4f}")
    logger.info(f"Gemini {strategy}: {total_input_tokens}+{total_output_tokens} tokens, ${cost:.4f}")

    # Aggregate Gemini scores
    scores = [r["gemini_judgment"].get("score", 0) for r in strategy_results["per_query"] if "error" not in r.get("gemini_judgment", {})]
    answerable = [r["gemini_judgment"].get("answerable", False) for r in strategy_results["per_query"] if "error" not in r.get("gemini_judgment", {})]
    if scores:
        strategy_results["metrics"]["gemini_avg_score"] = np.mean(scores)
        strategy_results["metrics"]["gemini_answerable_pct"] = np.mean(answerable) * 100

    return strategy_results


def print_comparison(paragraph_results, sentence_results, k_values):
    """Print side-by-side comparison table."""
    print("\n" + "=" * 70)
    print("RETRIEVAL EVALUATION RESULTS")
    print("=" * 70)

    print(f"\n{'Metric':<30} {'Paragraph':>15} {'Sentence':>15}")
    print("-" * 60)

    pm = paragraph_results.get("metrics", {})
    sm = sentence_results.get("metrics", {})

    for k in k_values:
        print(f"{'Recall@' + str(k):<30} {pm.get(f'recall@{k}', 0):>14.1%} {sm.get(f'recall@{k}', 0):>14.1%}")
    print()
    for k in k_values:
        print(f"{'Article Recall@' + str(k):<30} {pm.get(f'article_recall@{k}', 0):>14.1%} {sm.get(f'article_recall@{k}', 0):>14.1%}")
    print()
    print(f"{'MRR':<30} {pm.get('mrr', 0):>14.4f} {sm.get('mrr', 0):>14.4f}")

    # By difficulty
    print()
    for diff in ["easy", "medium", "hard"]:
        key = f"mrr_{diff}"
        if key in pm or key in sm:
            print(f"{'MRR (' + diff + ')':<30} {pm.get(key, 0):>14.4f} {sm.get(key, 0):>14.4f}")

    # Gemini scores if available
    if "gemini_avg_score" in pm or "gemini_avg_score" in sm:
        print()
        print(f"{'Gemini Avg Score (0-5)':<30} {pm.get('gemini_avg_score', 0):>14.2f} {sm.get('gemini_avg_score', 0):>14.2f}")
        print(f"{'Gemini Answerable %':<30} {pm.get('gemini_answerable_pct', 0):>13.1f}% {sm.get('gemini_answerable_pct', 0):>13.1f}%")

    # Show worst performing queries
    print("\n" + "=" * 70)
    print("WORST PERFORMING QUERIES (MRR=0, not found in top results)")
    print("=" * 70)
    for strategy, results in [("paragraph", paragraph_results), ("sentence", sentence_results)]:
        misses = [r for r in results.get("per_query", []) if r["mrr"] == 0]
        if misses:
            print(f"\n  {strategy} ({len(misses)} misses):")
            for m in misses[:5]:
                print(f"    {m['id']}: {m['question'][:60]}...")


def main():
    parser = argparse.ArgumentParser(description="Evaluate RAG retrieval")
    parser.add_argument("--k", nargs="+", type=int, default=[1, 3, 5, 10])
    parser.add_argument("--gemini", action="store_true", help="Use Gemini to judge answer quality")
    args = parser.parse_args()

    # Load QA pairs
    qa_data = json.loads(QA_FILE.read_text(encoding="utf-8"))
    qa_pairs = qa_data["test_pairs"]
    print(f"Loaded {len(qa_pairs)} test questions")

    # Load model and embed questions
    print(f"\nLoading model: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
    model.eval()

    questions = [f"query: {qa['question']}" for qa in qa_pairs]
    print(f"Embedding {len(questions)} questions...")
    t0 = time.time()
    query_embeddings = embed_texts(questions, tokenizer, model)
    print(f"Done in {time.time() - t0:.1f}s")

    # Evaluate both strategies
    print(f"\nEvaluating paragraph strategy...")
    paragraph_results = evaluate_strategy("paragraph", qa_pairs, query_embeddings, args.k)

    print(f"\nEvaluating sentence strategy...")
    sentence_results = evaluate_strategy("sentence", qa_pairs, query_embeddings, args.k)

    # Optional Gemini judging
    if args.gemini:
        print(f"\nGemini answer judging...")
        print("  Paragraph:")
        paragraph_results = gemini_judge(qa_pairs, paragraph_results, "paragraph")
        print("  Sentence:")
        sentence_results = gemini_judge(qa_pairs, sentence_results, "sentence")

    # Print comparison
    print_comparison(paragraph_results, sentence_results, args.k)

    # Save results
    output = {
        "k_values": args.k,
        "total_questions": len(qa_pairs),
        "paragraph": paragraph_results,
        "sentence": sentence_results,
    }
    RESULTS_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2, default=float), encoding="utf-8")
    print(f"\nResults saved to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
