# RAG Chunking Techniques - Complete Reference (2025-2026)

## Overview

Chunking is one of the most impactful decisions in a RAG pipeline. The Vectara NAACL 2025 study showed chunking configuration has **as much influence on retrieval quality as embedding model choice**.

**Bottom line**: Start with recursive character splitting at 512 tokens + 50-100 token overlap (69% end-to-end accuracy). Add complexity only where measurements justify it.

---

## Techniques

### 1. Fixed-Size Chunking
Split by character or token count with optional overlap.

- **Token-based** preferred over character-based (aligns with LLM context windows)
- **Overlap**: 10-20% recommended (e.g., 50-100 tokens for 512-token chunks). Beyond 30% rarely helps.
- **Performance**: 67% end-to-end accuracy (FloTorch 2026 benchmark)
- **Use when**: Simple baseline, well-structured documents, cost-sensitive

### 2. Recursive Character Splitting
**The recommended default.** LangChain's `RecursiveCharacterTextSplitter`.

- Tries separators in order: `["\n\n", "\n", " ", ""]`
- Splits on paragraphs first, then sentences, then words
- **Performance**: 69% end-to-end accuracy (best among 7 strategies in FloTorch benchmark)
- **Use when**: General-purpose text, establishing baseline

### 3. Semantic Chunking
Uses embedding similarity between consecutive sentences to detect topic shifts.

**Breakpoint methods**:
| Method | Threshold |
|--------|-----------|
| Percentile | 80th-95th percentile of cosine distances |
| Standard Deviation | X > 3.0 std above mean |
| IQR | Scaling factor 1.5 |

**Critical paradox**:
- 91.9% retrieval recall (best) BUT only 54% end-to-end accuracy (worst)
- Chunks average only 43 tokens - too small for good generation
- Vectara NAACL 2025: "computational costs not justified by consistent gains" on natural documents
- **Exception**: On high-topic-diversity datasets, semantic chunking wins (NQ: 63.93% vs fixed 43.79%)

**Use when**: Content with high topic diversity, finance/legal domains (with minimum chunk size floor of 200+ tokens)

### 4. Document-Aware Chunking
Splits based on document structure.

| Format | Approach | Notes |
|--------|----------|-------|
| **Markdown** | Split by headers (#, ##, ###) | Chunks retain header hierarchy |
| **HTML** | Split by semantic tags (p, div, section) | Convert to markdown first for best results |
| **Code** | AST-based (tree-sitter) | +4.3 Recall@5 on RepoEval. cAST framework (EMNLP 2025) |
| **PDF** | Page-level | Winner in NVIDIA benchmark (0.648 accuracy, lowest variance) |

**Hybrid approach**: Structure-aware first (headers), then recursive on oversized chunks.

### 5. Sentence/Paragraph-Based Chunking
Uses NLP libraries (NLTK punkt, spaCy) for linguistically-aware splitting.

- Group consecutive sentences until target chunk size reached
- ColBERT v2 + SentenceSplitter was **top-performing combination** (~0.3123 MRR)
- **Use when**: Q&A, legal documents, short-form content

### 6. Agentic/LLM-Based Chunking
Uses an LLM to determine chunk boundaries based on content understanding.

- Extract propositions (atomic facts), group into coherent chunks
- Clinical study: **87% accuracy** vs **13% for fixed-size baseline**
- **TopoChunker** (2026): topology-aware agentic chunking
- **Use when**: High-value, complex documents (legal contracts, research papers, compliance). Justifies compute cost.

### 7. Late Chunking (Jina AI)
Reverses traditional pipeline: embed full document first, then chunk the embeddings.

- **Traditional**: Document -> chunk -> embed each independently
- **Late chunking**: Document -> embed entire doc -> apply pooling over chunk spans
- Resolves anaphoric references ("it," "the city") that are ambiguous in isolated chunks
- Requires long-context embedding models (e.g., Jina Embeddings 2, 8K context)
- Trade-off: Higher efficiency but may sacrifice relevance vs contextual retrieval

### 8. Parent-Child / Hierarchical Chunking
Two-tier index: small chunks for retrieval precision, large parent chunks for context.

- **Child chunks**: 200-400 tokens (retrieval)
- **Parent chunks**: 800-1000 tokens (context for LLM)
- Retrieval matches child, returns parent
- LangChain: `ParentDocumentRetriever`
- **Solves**: The fundamental tension between small chunks (better retrieval) and large chunks (better generation)

---

## Chunk Size Guidelines

| Size | Best For | Evidence |
|------|----------|----------|
| 64-128 tokens | Not recommended for most uses | NVIDIA: 128 tokens showed poorest overall performance |
| 256 tokens | Factoid queries (names, dates) | Good precision, may lack context |
| **400-512 tokens** | **General-purpose sweet spot** | FloTorch: 69% accuracy. Chroma: 88-89% recall |
| 512-1024 tokens | Analytical, multi-hop queries | FinanceBench: 1024 tokens at 0.579 accuracy |
| 2048+ tokens | Diminishing returns | Performance drops. "Context cliff" around 2,500 tokens |

**Key finding**: Oracle experiments show 20-40% headroom when selecting optimal chunk size per query vs any fixed size. No single size dominates.

---

## Overlap Guidelines

| Chunk Size | Recommended Overlap |
|-----------|-------------------|
| 256 tokens | 25-50 tokens |
| 512 tokens | 50-100 tokens |
| 1024 tokens | 100-200 tokens |

Beyond 30% overlap: negligible improvement, increased storage costs.

---

## Technique Selection by Use Case

| Use Case | Technique | Chunk Size |
|----------|----------|------------|
| General Q&A | Recursive character splitting | 400-512 tokens |
| Factoid Q&A | Sentence-based or recursive | 256-512 tokens |
| Multi-hop / analytical | Recursive or parent-child | 512-1024 tokens |
| Summarization | Semantic or hierarchical | 512-1024 tokens |
| Code repositories | AST-based (cAST) | Function/class boundaries |
| Legal documents | Agentic/adaptive or sentence-based | 512-1024 tokens |
| Financial documents | Page-level or 1024-token recursive | 1024 tokens |
| Medical / clinical | Adaptive chunking | Topic-aligned |
| Technical docs (Markdown) | Header-based + recursive fallback | Section-aligned |
| PDFs with tables | Page-level chunking | Page boundaries |
| Cross-reference heavy docs | Late chunking or contextual retrieval | 512 tokens |
| High-value enterprise docs | Agentic/LLM-based | Dynamic |

---

## Emerging Best Practices

1. **Contextual Retrieval** (Anthropic): Prepend LLM-generated context to each chunk before embedding. -35% retrieval failure (embeddings), -49% (+BM25), -67% (+reranking). Cost: ~$1.02/M tokens.

2. **Multi-scale indexing** (AI21 Labs): Index same corpus at multiple sizes (100, 200, 500 tokens), aggregate with RRF. Improves retrieval 1-37%.

3. **Mix-of-Granularity (MoG)** (COLING 2025): Router dynamically selects optimal chunk granularity per query.

---

## Key Takeaways

- **Semantic chunking is overrated for most use cases** - retrieves well but produces chunks too small for generation (54% vs 69% end-to-end)
- **For high-value domains** (legal, medical, financial), agentic chunking justifies the cost (87% vs 13% baseline)
- **Always benchmark on your actual data** - chunking config matters as much as embedding model choice
- **Consider multi-scale indexing** as low-effort improvement
