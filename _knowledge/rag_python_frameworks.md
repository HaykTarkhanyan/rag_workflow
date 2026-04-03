# Python RAG Frameworks - Comparison (2025-2026)

## Quick Comparison Matrix

| Framework | GitHub Stars | PyPI Downloads/mo | Learning Curve | Production Ready | Primary Focus |
|---|---|---|---|---|---|
| **LangChain** | ~100k | ~225M | Steep | Yes | General LLM orchestration + agents |
| **LlamaIndex** | ~48k | ~10M | Moderate | Yes | Data indexing + retrieval |
| **Haystack** | ~21.5k | ~700k | Moderate | Yes (enterprise) | Production NLP pipelines |
| **DSPy** | ~19k | ~5.3M | Steep (research) | Maturing | Programmatic prompt optimization |
| **Semantic Kernel** | ~27.5k | ~2.8M | Moderate | Yes (MS-backed) | Enterprise AI orchestration |
| **Unstructured** | ~14k | ~5.2M | Low | Yes | Document ETL/parsing |
| **txtai** | ~10.5k | ~57k | Low | Small-scale | All-in-one lightweight RAG |
| **RAGatouille** | ~3.9k | ~26k | Low | Experimental | ColBERT late-interaction |

---

## Detailed Analysis

### LangChain
- 70+ LLM providers, 700+ integrations
- LangGraph for stateful agentic workflows, LangSmith for tracing
- **Strengths**: Unmatched ecosystem, massive community, abundant tutorials
- **Weaknesses**: ~10ms overhead, opaque stack traces, frequent breaking changes, overkill for simple RAG
- **Best for**: Complex multi-step agentic apps integrating many tools/APIs

### LlamaIndex
- Purpose-built for RAG with sophisticated indexing (tree, keyword, vector, graph)
- 40% faster retrieval than LangChain. LlamaParse for document parsing
- **Strengths**: Simplest API for pure RAG (`as_query_engine()`), superior retrieval quality, best document handling
- **Weaknesses**: Query engine can be a black box, less suited for complex agents
- **Best for**: Pure document Q&A and RAG. When retrieval quality is top priority

### Haystack (deepset)
- Pipeline-as-configuration: serialize to YAML, version, deploy without code changes
- Lowest token usage (~1.57k tokens) and low overhead (~5.9ms)
- **Strengths**: Most production-oriented, pipeline clarity, excellent for governance
- **Weaknesses**: Smallest community, Python-only, v1->v2 migration was disruptive
- **Best for**: Enterprise deployments requiring reproducibility, auditability, governance

### DSPy (Stanford NLP)
- Define signatures (input/output specs), optimizers automatically find best prompts
- Lowest framework overhead (~3.53ms)
- **Strengths**: Eliminates manual prompt engineering, dramatically outperforms hand-tuned prompts
- **Weaknesses**: Steep learning curve, requires labeled data, fewer production examples
- **Best for**: Complex reasoning pipelines, research, prompt engineering bottlenecks

### Semantic Kernel (Microsoft)
- Multi-language (C#, Python, Java), deep Azure/OpenAI integration
- Plugin architecture for extending with custom tools
- **Strengths**: Natural for Azure shops, strong enterprise governance, stable API
- **Weaknesses**: Python SDK less mature, smaller RAG community, Azure-centric
- **Best for**: Enterprise teams in Microsoft/Azure ecosystem

### Unstructured
- Best-in-class multi-format document parsing (PDF, DOCX, PPTX, HTML, images)
- Layout-aware chunking, OCR integration, table extraction
- **NOT a full RAG framework** - handles ingestion/parsing only
- **Best for**: Any RAG pipeline needing real-world document handling

### txtai
- All-in-one: embeddings, vector DB, RAG, LLM orchestration in one package
- YAML-based workflow configuration
- **Best for**: Solo developers, learning RAG, small projects needing multiple NLP capabilities

### RAGatouille / ColBERT
- Token-level matching catches nuances single-vector embeddings miss
- Easy fine-tuning on domain data
- **Best for**: Research or specialized domains where retrieval quality is paramount

### Custom / Minimal Approach
Stack: `anthropic`/`openai` + `chromadb`/`faiss-cpu` + `sentence-transformers`
- **Strengths**: Maximum control, debuggability, zero overhead, no framework lock-in
- **Weaknesses**: Must implement everything yourself
- **Best for**: Simple prototypes, maximum control, unusual requirements

---

## Recommendations by Project Type

### Prototype / MVP
- **Primary**: LlamaIndex (fastest to working RAG) or custom minimal
- **Vector DB**: ChromaDB (zero config)
- **Doc parsing**: Unstructured (if complex docs)

### Production Application
- **Primary**: LangChain + LangGraph (if agentic) or Haystack (if pipeline-focused)
- **Vector DB**: Qdrant or Milvus
- **Doc parsing**: Unstructured
- **Tracing**: LangSmith or custom OpenTelemetry

### Research / Experimentation
- **Primary**: DSPy (auto optimization) + RAGatouille (retrieval quality)
- **Vector DB**: FAISS
- **Evaluation**: DSPy optimizers or RAGAS

### Enterprise / Microsoft Shop
- **Primary**: Semantic Kernel (Azure-centric) or Haystack (vendor-neutral)
- **Vector DB**: Azure AI Search or Qdrant Cloud

### Solo Developer / Learning
- **Primary**: txtai (all-in-one) or custom minimal
- **Vector DB**: ChromaDB

---

## Key Trends

1. LangChain and LlamaIndex converging - LangChain adding retrieval, LlamaIndex adding agents
2. Graph RAG rising (LightRAG, Microsoft GraphRAG)
3. Agentic RAG becoming dominant - RAG embedded in agent loops
4. Custom approaches gaining respect as ecosystem matures
5. DSPy adoption accelerating with v3.x
