# RAG Architecture & Patterns - Complete Reference (2025-2026)

## Pipeline Stages

### 1. Ingestion
- **Document parsing**: Extract text from PDFs, HTML, Markdown, etc. Tools: Unstructured.io, LlamaParse, Docling
- **Metadata extraction**: Source, date, author, section headers - critical for filtering
- **Cleaning**: Remove boilerplate, duplicates, normalize encoding
- **Best practice**: Preserve document structure (headings, tables, lists). Multimodal pipelines handling images + tables + text are becoming standard

### 2. Chunking
Split documents into retrieval units. One of the most impactful decisions in a RAG pipeline. See `rag_chunking_techniques.md` for detailed coverage.

### 3. Embedding
Convert chunks into dense vectors.

**Leading models (2025-2026)**:
| Model | Dimensions | Context | Notes |
|-------|-----------|---------|-------|
| OpenAI text-embedding-3-large | 3072 | 8K | Matryoshka (variable dim), strong general-purpose |
| Cohere embed-v3/v4 | 1024 | 512 | Multiple input types, native quantization |
| BGE-M3 (BAAI) | 1024 | 8K | Open-source, supports dense + sparse + multi-vector simultaneously |
| Jina Embeddings v3 | 1024 | 8K | Task-specific LoRA adapters, multilingual |
| Nomic Embed | 768 | 8K | Open-source, competitive with proprietary |
| Voyage AI | varies | varies | Specialized models for code (voyage-code-3) |
| Metric-AI armenian-text-embeddings-2 | 768/1024 | 512 | Armenian language specialized |

**Best practice**: Use query/document asymmetric embedding. Fine-tuning on domain data improves retrieval 5-15%.

### 4. Indexing
Organize embeddings for efficient similarity search.

**Index types**:
- **HNSW**: Dominant in 2025. >95% recall, sub-ms query times. Memory-intensive
- **IVF**: Good for 100M+ vectors. Lower memory than HNSW
- **Product Quantization (PQ)**: 4-16x memory reduction, trades recall
- **Binary/Scalar quantization**: 8-32x memory reduction

**Best practice**: Hybrid indexing - combine dense vector + sparse keyword (BM25) indexes. Use Reciprocal Rank Fusion (RRF) to combine results.

### 5. Retrieval
**Methods** (in order of increasing sophistication):
1. **Dense retrieval**: Cosine similarity over embeddings
2. **Sparse retrieval**: BM25 or SPLADE. Excels at exact keyword matching
3. **Hybrid retrieval**: Dense + sparse with RRF. Consistently outperforms either alone by 5-15%
4. **Multi-vector (ColBERT)**: Per-token embeddings, fine-grained similarity. Higher recall but 50-100x more storage
5. **Two-stage re-ranking**: Retrieve top 20-50 with bi-encoder, re-rank with cross-encoder to top 3-10

**Industry standard pipeline**: Query -> hybrid search (dense + sparse) -> retrieve top 20-50 -> cross-encoder re-rank -> top 3-10 to LLM

### 6. Generation
- Keep retrieved context focused (5-10 chunks). "Lost in the middle" effect with long contexts
- Place most relevant chunks first and last (primacy/recency bias)
- Include source metadata for attribution/citation
- Use grounding instructions: "only use provided context, say I don't know when insufficient"

---

## RAG Patterns

### Naive RAG
Query -> Retrieve -> Generate. No query transformation, no re-ranking, no validation.
- **When to use**: Prototyping, simple Q&A over well-structured corpora
- **Limitations**: Poor retrieval quality, hallucination, can't handle multi-hop questions

### Advanced RAG
Adds pre-retrieval and post-retrieval optimizations:
- **Pre-retrieval**: Query rewriting (HyDE, multi-query), metadata filtering, hierarchical indexing
- **Post-retrieval**: Re-ranking, context compression, diversity filtering (MMR)
- **When to use**: Production systems where accuracy matters

### Modular RAG
Composable system of interchangeable modules with routing and iteration.
- **Routing**: Dynamically choose modules based on query type
- **Iteration**: Multiple retrieval-generation cycles
- **When to use**: Complex production systems, multi-source retrieval
- **Frameworks**: LangGraph, LlamaIndex Workflows, Haystack 2.0

---

## Advanced Techniques

### Query Transformation
| Technique | How It Works | Best For |
|-----------|-------------|----------|
| **HyDE** | LLM generates hypothetical answer, embed that for retrieval | Knowledge-intensive queries |
| **Multi-Query** | Generate multiple reformulations, retrieve for each, merge | Increasing recall (10-20% improvement) |
| **Step-Back Prompting** | Generate abstract version of query, retrieve both | Science/technical questions |
| **Query Decomposition** | Break complex query into sub-questions | Multi-hop reasoning |
| **Query Routing** | Classify query, route to different retrieval strategies | Diverse query types |

### Self-RAG (Asai et al., 2023)
LLM decides: (1) whether retrieval is needed, (2) evaluates passage relevance, (3) generates, (4) checks faithfulness. Uses reflection tokens. Outperformed standard RAG on PopQA, TriviaQA, ASQA.

### Corrective RAG (CRAG)
Adds retrieval evaluator that grades quality: Correct -> proceed; Incorrect -> fallback to web search; Ambiguous -> refine and supplement. Makes system robust to retrieval failure.

### Agentic RAG
LLM as agent that dynamically decides what actions to take. Key patterns:
- **Routing agent**: Classifies query, routes to appropriate tool
- **Multi-step agent**: Plans retrieval and reasoning sequences
- **Tool-use RAG**: Retrieval as a tool the LLM calls when needed
- **Multi-agent RAG**: Separate agents for retrieval, fact-checking, synthesis

### Graph RAG (Microsoft, 2024)
1. LLM extracts entities and relationships from chunks
2. Build knowledge graph
3. Community detection (Leiden algorithm)
4. LLM summarizes communities at multiple hierarchy levels
5. Query: global queries use community summaries, local queries combine graph + vector

**Excels at**: "What are the main themes?" - global queries that standard RAG fails on.
**Variants**: LightRAG, nano-GraphRAG, RAPTOR (recursive abstractive tree)

### Contextual Retrieval (Anthropic)
Prepend LLM-generated context summary to each chunk before embedding. Results:
- 49% reduced retrieval failure (embeddings + BM25)
- 67% reduction with re-ranking added
- Cost: ~$1.02 per million document tokens

---

## Evaluation

### RAGAS Framework
| Metric | What It Measures | Target |
|--------|-----------------|--------|
| Faithfulness | Answer supported by retrieved context only | >0.9 |
| Answer Relevance | Answer addresses the question | >0.8 |
| Context Precision | Relevant chunks ranked higher | >0.8 |
| Context Recall | All needed information retrieved | >0.8 |

### Component-Level Metrics
- **Retrieval**: Hit rate, MRR, NDCG, MAP
- **Generation**: BERTScore, LLM-as-Judge (preferred in 2025)
- **End-to-end**: Exact Match, F1, human preference

### Best Practices
1. Build "golden evaluation set" of 50-200 questions with ground truth BEFORE optimizing
2. Run all pipeline changes against this set
3. Track retrieval latency (p50, p95, p99)
4. Monitor user feedback (thumbs up/down)
5. A/B test pipeline changes

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Wrong chunk size | Test 3-5 sizes against eval set. Use hierarchical chunking as default |
| Embedding model mismatch | Fine-tune on domain data. Use contextual retrieval |
| Lost in the middle | Limit to 5-10 chunks. Place best first and last. Use re-ranking |
| Keyword/entity gaps | Always use hybrid search (dense + sparse) |
| Hallucination over context | Grounding instructions, citations, Self-RAG/CRAG |
| No re-ranking | Always add cross-encoder re-ranker (highest-ROI improvement) |
| No evaluation framework | Build eval sets first. Automate in CI/CD |
| Premature optimization | Start with naive RAG, measure failures, add complexity where justified |

---

## Field Direction (2025-2026)

1. **Agentic RAG** becoming dominant - LLM decides when/what/how to retrieve
2. **Hybrid search + re-ranking** is the baseline, not an optimization
3. **Graph RAG** gaining traction for complex reasoning
4. **Evaluation-driven development** is essential
5. **Multimodal RAG** (images, tables, text together) rapidly maturing
6. **Long-context models** (1-2M tokens) complement, not replace, RAG
7. **Fine-tuning embeddings** on domain data becoming standard practice
