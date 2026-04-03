# Vector Databases & Retrieval - Comparison (2025-2026)

## Quick Comparison

| Database | Open Source | Deployment | Scale | Hybrid Search | Filtering | GitHub Stars |
|---|---|---|---|---|---|---|
| **FAISS** | Yes (MIT) | Embedded | Billions (single node) | No | No native | ~33k |
| **ChromaDB** | Yes (Apache 2.0) | Embedded/Cloud | Millions | Basic | Metadata where | ~18k |
| **Qdrant** | Yes (Apache 2.0) | Self-hosted/Cloud | Billions (distributed) | Yes (sparse vectors) | Excellent (payload) | ~22k |
| **Pinecone** | No (proprietary) | Cloud only | Billions (serverless) | Yes | Metadata | N/A |
| **Weaviate** | Yes (BSD-3) | Self-hosted/Cloud | Large (distributed) | Yes (best BM25+vector) | GraphQL-based | ~14k |
| **Milvus** | Yes (Apache 2.0) | Self-hosted (K8s)/Cloud | Tens of billions | Yes | Boolean expressions | ~32k |
| **pgvector** | Yes (PostgreSQL) | Anywhere PostgreSQL runs | ~10M vectors | SQL tsvector + vector | Full SQL WHERE | ~13k |
| **Elasticsearch** | Source-available | Self-hosted/Cloud | Massive | Yes (best BM25 + kNN) | World-class query DSL | ~72k |
| **LanceDB** | Yes (Apache 2.0) | Embedded/Serverless | Large (object storage) | Yes (Tantivy BM25) | SQL-like | ~5k |
| **Redis** | Source-available | Self-hosted/Cloud | In-memory limited | Yes (RediSearch) | Tags, numerics, geo | ~68k |

---

## Detailed Analysis

### FAISS (Meta)
- **Library, not a database**. No persistence, no API server, no metadata filtering
- GPU-accelerated, raw performance king. Algorithm flexibility (IVF, HNSW, PQ)
- **Best for**: Research, offline batch processing, embedded in ML pipelines
- **Cost**: Free. Compute/memory only

### ChromaDB
- Zero-config: `pip install chromadb` and go. 2025 Rust rewrite (4x performance)
- Not designed for 50M+ vectors
- **Best for**: Prototyping, learning, MVPs under 10M vectors
- **Cost**: Free self-hosted. Cloud is usage-based

### Qdrant
- Rust-based. Rich payload filtering applied DURING ANN search (not post-filter)
- Supports sparse vectors natively for true hybrid search. Multi-vector per point
- **Best for**: Production RAG with hybrid search and filtering. Best balance of features/performance/cost
- **Cost**: Free self-hosted. Cloud ~$25/month small clusters

### Pinecone
- Fully managed, zero ops. Serverless tier scales automatically
- **Best for**: Teams wanting zero operational overhead with budget
- **Cost**: Serverless read/write units. Typical $100-1000+/month production

### Weaviate
- **Best out-of-box hybrid search** with configurable fusion (ranked fusion, relative score fusion)
- GraphQL-based API. Strong multi-tenancy
- **Best for**: Applications needing best hybrid search, multi-tenant SaaS
- **Cost**: Free self-hosted. Cloud ~$25/month+

### Milvus / Zilliz
- Designed for massive scale. Disaggregated storage/compute. K8s-native
- **Most scalable open-source option** for tens of billions of vectors
- **Best for**: Large-scale enterprise. Teams with K8s expertise
- **Cost**: Free self-hosted (but K8s overhead). Zilliz Cloud ~$65+/month

### pgvector (PostgreSQL)
- Just add extension to existing PostgreSQL. Full SQL power
- HNSW indexes work well up to ~10M vectors
- **Best for**: Teams already on PostgreSQL. "Just add vector search to my existing app"
- **Cost**: Free (uses existing PostgreSQL)

### Elasticsearch / OpenSearch
- Most mature hybrid search (gold standard BM25 + kNN vector). RRF built-in
- Most powerful filtering/querying of any option
- **Best for**: Orgs already on Elasticsearch. Full-text search quality paramount
- **Cost**: Self-hosted free but operationally expensive. Elastic Cloud ~$95/month

### LanceDB
- Embedded, serverless-friendly. Data in object storage (S3/GCS) in Lance columnar format
- Potentially cheapest option at scale for read-heavy workloads
- **Best for**: Cost-sensitive, serverless/edge, multimodal data. Emerging/promising
- **Cost**: Very low. Storage costs only

### Redis Vector Search
- In-memory, low-latency. RediSearch combines full-text + vector natively
- RAM-limited scalability
- **Best for**: Apps already using Redis. Real-time low-latency needs. Caching + search
- **Cost**: RAM-based pricing. $100+/month moderate workloads

---

## Retrieval Strategies

### Dense Retrieval
Cosine similarity over embeddings. Semantic matching, handles synonyms.
Weakness: misses exact keywords, rare terms, product codes.

### Sparse Retrieval (BM25)
Traditional keyword-based. Exact match strength. No embeddings needed.
**SPLADE/learned sparse**: Model-generated sparse representations. Bridges gap between sparse and dense. Gaining traction.

### Hybrid Search (BEST PRACTICE)
Dense + sparse combined. **5-15% recall improvement** over dense-only. Considered baseline for production.
- **RRF**: Simple, robust, parameter-free
- **Weighted linear**: Tunable alpha (e.g., 0.7 dense + 0.3 sparse)
- **Relative Score Fusion**: Normalizes scores before combining

### Re-ranking (HIGHEST ROI)
Two-stage: retrieve top 20-100 cheaply, re-rank with expensive model to top 3-10.

| Reranker | Type | Notes |
|----------|------|-------|
| **Cohere Rerank v3.5** | API | State-of-the-art, multilingual, ~$2/1k searches |
| **BGE-reranker-v2.5** | Self-hosted | Strong open-source, free |
| **Jina Reranker v2** | Self-hosted | Strong open-source, free |
| **cross-encoder/ms-marco-MiniLM** | Self-hosted | Classic, 50-200ms for 100 docs |
| **ColBERTv2** | Self-hosted | Late-interaction, faster than cross-encoders |

---

## Query Transformation

| Technique | Process | Cost | Best For |
|-----------|---------|------|----------|
| **HyDE** | LLM generates hypothetical answer, embed for retrieval | +1 LLM call | Knowledge-intensive queries |
| **Multi-Query** | Generate 3-5 query reformulations, retrieve each, merge | +N retrieval calls | Increasing recall (10-20% boost) |
| **Step-Back** | Generate abstract version of query, retrieve both | +1 LLM call | Science/technical questions |
| **Decomposition** | Break complex query into sub-questions | +N LLM calls | Multi-hop reasoning |

---

## Recommendation Matrix

### Prototype (0-10K docs)
- **Fastest start**: ChromaDB
- **Already on PostgreSQL**: pgvector
- **Zero cost**: FAISS + rank_bm25

### Startup (10K-10M docs)
- **Best balance**: Qdrant (hybrid search, filtering, reasonable cost)
- **Minimize ops**: Pinecone Serverless
- **Hybrid search priority**: Weaviate
- **Budget**: pgvector on managed PostgreSQL

### Growth (10M-1B docs)
- **Max scale, open source**: Milvus
- **Managed scalable**: Qdrant Cloud or Zilliz Cloud
- **Existing search infra**: Elasticsearch/OpenSearch
- **Cost optimization**: LanceDB on object storage

### Enterprise (1B+ docs)
- **Max control**: Milvus + Elasticsearch
- **Managed + support**: Pinecone Enterprise or Zilliz Enterprise
- **Compliance/data residency**: Qdrant or Weaviate self-hosted

---

## Universal Recommendations

1. **Always use hybrid search** (dense + sparse) in production
2. **Always add a reranker** - typically the highest-ROI improvement
3. **Start simple, add complexity** - measure at each step
4. **Chunking strategy matters more than vector DB choice** for most applications

---

## Key Trends

1. Traditional DBs adding vector search, vector DBs adding full-text search - lines blurring
2. SPLADE (learned sparse) replacing BM25 in cutting-edge systems
3. ColBERT family (multi-vector/late interaction) gaining as quality-latency sweet spot
4. Serverless vector DBs (Pinecone Serverless, LanceDB) reducing costs
5. Embedding model quality improvements (Matryoshka, native quantization) benefit all DBs
