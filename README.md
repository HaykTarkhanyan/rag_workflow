# RAG Workflow

RAG system with Armenian embeddings + Claude Code workflow for RAG development by Metric AI.

## Project Goals

1. **RAG system** -- Retrieval-augmented generation pipeline leveraging Metric-AI's Armenian text embeddings models
2. **Claude Code workflow** -- Hooks, skills, agents, and MCP servers to streamline RAG development

## Progress

### Done

- [x] Repo initialized, project structure set up
- [x] Armenian embeddings demo (`armenian_embeddings_demo.py`) -- tests both `base` (768d) and `large` (1024d) models
- [x] Both Metric-AI embedding models downloaded and cached locally
- [x] Knowledge base built in `_knowledge/` (9 reference docs):
  - RAG architecture, chunking, frameworks, vector DBs
  - Claude Code hooks, skills, agents, MCP servers
  - Web scraping tools & libraries for RAG ingestion
- [x] MCP servers installed: **Playwright** (browser automation) + **Fetch** (URL-to-markdown)
- [x] First scraper: `scrape_infocom.py` -- 65 Infocom.am investigation articles (600K chars, full metadata)
  - Caching, `--force` / `--parse` flags, handles two Elementor templates
- [x] Learnings documented in `_learning/` (scraping gotchas, BeautifulSoup pitfalls)
- [x] Corpus stats script (`corpus_stats.py`) -- word/sentence/paragraph distributions, token estimates, metadata coverage
- [x] Chunking script (`chunk_articles.py`) -- two strategies:
  - Sentence-group (~110 tokens, 1,390 chunks) -- matches 128-token training window
  - Paragraph-group (~350 tokens, 421 chunks) -- uses more of 512-token inference limit
- [x] Article IDs added (e.g., `infocom_10007787`)
- [x] Embedding + indexing script (`embed_and_index.py`) -- Metric-AI large (1024d) + ChromaDB
- [x] Gemini prompt for generating test QA pairs (`prompts/generate_test_qa_pairs.md`)
- [ ] **In progress:** Paragraph embeddings running (~14 min CPU)

### Next

- [ ] Generate QA test pairs with Gemini (Armenian)
- [ ] Build evaluation script (recall@k, MRR, precision)
- [ ] Compare sentence vs paragraph chunking retrieval quality
- [ ] Build retrieval/query interface
- [ ] Scrape more data sources for RAG corpus
- [ ] Build Claude Code skills for common RAG operations

## Tech Stack

- **Language**: Python 3.10
- **Package manager**: uv
- **Embeddings**: Metric-AI Armenian Text Embeddings v2 (base 768d, large 1024d)
- **Scraping**: httpx + BeautifulSoup, Playwright MCP, Fetch MCP
- **Vector DB**: ChromaDB (persistent, cosine similarity)
- **Knowledge base**: `_knowledge/` folder (markdown reference docs)

## Structure

```
rag_workflow/
  _knowledge/          # Reference docs (RAG, Claude Code, scraping)
  _learning/           # Documented approaches, mistakes, and fixes
  scraped_data/        # Scraped articles (JSON) + HTML cache
  scrape_infocom.py    # Infocom.am investigation article scraper
  corpus_stats.py      # Corpus statistics for chunking/embedding decisions
  chunk_articles.py    # Chunking (sentence-group and paragraph-group strategies)
  embed_and_index.py   # Embed chunks + index into ChromaDB
  prompts/             # Prompts for external models (Gemini QA generation)
  test_data/           # QA test pairs for retrieval evaluation
  armenian_embeddings_demo.py  # Embeddings model demo
  CLAUDE.md            # Project guidelines for Claude Code
```
