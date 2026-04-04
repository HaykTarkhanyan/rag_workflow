# Codebase Audit

Detailed review of all scripts, configs, and project structure.
Date: 2026-04-04

---

## Bugs

### BUG-1: `embed_and_index.py` catches wrong exception on delete_collection (line 149)

```python
except ValueError:
    pass
```

ChromaDB raises `chromadb.errors.NotFoundError`, not `ValueError`. This was already fixed in `load_embeddings.py` (uses `except Exception`) but not in `embed_and_index.py`. If someone runs `--reset` on a fresh DB, it will crash instead of gracefully continuing.

**Fix:** Change to `except Exception: pass`.

### BUG-2: `evaluate_retrieval.py` embeds all 30 questions in one batch (line 71-72)

```python
def embed_texts(texts, tokenizer, model):
    batch = tokenizer(texts, max_length=512, padding=True, truncation=True, return_tensors="pt")
```

This tokenizes all 30 questions into a single batch. With 30 questions this works, but it will OOM if used with more questions or longer texts. The `embed_and_index.py` version correctly batches in groups of 8.

**Fix:** Add batching, or reuse `embed_batch` from `embed_and_index.py`.

### BUG-3: `chunk_articles.py` join separator heuristic is fragile (line 93)

```python
chunk_text = " ".join(chunk_units) if len(units[0].split("\n")) <= 1 else "\n\n".join(chunk_units)
```

This checks `units[0]` (the first unit of the *entire article*) to decide the separator for *all chunks*. If the first sentence happens to contain a newline, all chunks will use `\n\n` separator even for sentence strategy. Should check the strategy parameter directly.

**Fix:** Pass strategy into `chunk_by_units` or use a separator parameter.

### BUG-4: `chunk_articles.py` mutates the input data (line 187)

```python
article["article_id"] = article_id
```

This writes article_id back into the loaded JSON dict, then saves the modified data back to `infocom_investigations.json` (line 248). Running `chunk_articles.py` twice with different strategies will overwrite the source file each time. This side effect is documented but surprising.

### BUG-5: `scrape_infocom.py` line 188 uses `get_text(strip=True)` inconsistently

```python
if el and len(el.get_text(strip=True)) > 100:
```

This uses `get_text(strip=True)` for the length check, but `_extract_from_element` uses `_get_text_safe` for actual extraction. The length check could undercount due to stripped spaces. Not a critical bug but inconsistent with the lesson learned.

### BUG-6: `corpus_stats.py` has unused variable `all_words` (line 52, 70)

```python
all_words = []
...
all_words.extend(content.split())
```

`all_words` is populated but never read. Wasted memory for large corpora.

---

## Security

### SEC-1: `.env` with real API key was committed to git history

The `.env` contains a real API key. **Verified:** `git log --all --full-history -- .env` returns empty -- the file was never committed. However, the key appeared in system reminders during the conversation. No action needed, but worth being aware of.

### SEC-2: Secret scanner regex is too narrow

`check-no-secrets.sh` checks for `AIza...`, `sk-...`, and `GEMINI_API_KEY=`. This misses:
- `gsk_` (Groq keys)
- `hf_` (HuggingFace tokens)
- Generic patterns like `password=`, `secret=`, `token=`
- Base64-encoded keys

### SEC-3: No `.env.example` file

New contributors won't know what env vars are needed without reading the code.

---

## Code Duplication

### DUP-1: `average_pool` is defined in 3 files

Identical function in `armenian_embeddings_demo.py`, `embed_and_index.py`, and `evaluate_retrieval.py`. Should be in a shared module.

### DUP-2: ChromaDB metadata flattening is duplicated

The metadata dict construction (article_id, title, author, etc.) is copy-pasted identically in `embed_and_index.py` (lines 200-209) and `load_embeddings.py` (lines 79-89). Any field change must be updated in both places.

### DUP-3: Model loading code is duplicated

`load_model()` in `embed_and_index.py` and the inline model loading in `evaluate_retrieval.py` (lines 314-317) do the same thing.

---

## Design Issues

### DESIGN-1: Large binary files committed to git

The `.npy` embedding files (5.7MB + 1.7MB) and chunk JSONs (4.5MB + 3.2MB) are tracked in git. These are derived artifacts that can be regenerated. Total ~16MB of binary/generated data in the repo. Consider:
- Adding `scraped_data/*.npy` to `.gitignore`
- Using Git LFS for large files
- Or documenting that these are intentionally tracked for convenience

### DESIGN-2: `embeddings_cache/` not in `.gitignore`

The per-chunk `.npy` cache files from `embed_and_index.py` are not gitignored. If someone runs the CPU embedding path, 421+ small `.npy` files would show as untracked.

### DESIGN-3: No shared module for embedding utilities

`average_pool`, model loading, and embedding functions are scattered across 3 files. A `utils/embeddings.py` module would eliminate duplication and ensure consistency.

### DESIGN-4: Token estimation is a rough heuristic

`estimate_tokens()` uses `word_count * 1.5` as a fixed multiplier. This is reasonable on average but can be off by 30-50% for individual chunks (Armenian compound words tokenize differently). The actual tokenizer is available but unused for counting. Consider:
- Using the real tokenizer for accurate counts (adds ~1s startup cost)
- Or documenting the known inaccuracy

### DESIGN-5: `text_for_embedding` includes title prefix but token estimate doesn't account for it

In `chunk_articles.py` line 153:
```python
chunk_text_for_embedding = f"passage: {prefix}. {rc['text']}"
```

The token estimate at line 98 is calculated on the raw chunk text, not the `text_for_embedding` which is longer (adds "passage: " + full title). This means actual token counts sent to the model are higher than estimated, potentially exceeding the 512-token limit for paragraph chunks.

### DESIGN-6: Hardcoded "infocom" in collection names and article IDs

Everything is `infocom_investigations_*` and `infocom_XXXXX`. When adding new sources, the naming scheme needs to be generalized.

### DESIGN-7: No logging in most scripts

CLAUDE.md requires Python logging, but only `evaluate_retrieval.py` uses it. All other scripts (`scrape_infocom.py`, `chunk_articles.py`, `corpus_stats.py`, `load_embeddings.py`) use bare `print()`.

---

## Hook Issues

### HOOK-1: Venv hook uses `-oP` (Perl regex) which may not work on Git Bash for Windows

```bash
CMD=$(echo "$TOOL_INPUT" | grep -oP '"command"\s*:\s*"[^"]*"' ...)
```

Git Bash on Windows ships a grep that may or may not support `-P` (Perl regex). If it doesn't, `$CMD` will be empty and the hook silently passes everything.

**Fix:** Use `-o` with extended regex (`-E`) instead, or use `sed`/`awk` for JSON extraction.

### HOOK-2: Venv hook regex doesn't match `PYTHONUNBUFFERED=1 python ...`

The regex `'^python[3.]?(\s|$)'` only matches commands starting with `python`. Commands like `PYTHONUNBUFFERED=1 python script.py` or `cd dir && python script.py` won't trigger the warning.

### HOOK-3: Stop hook fires on every stop, even trivial ones

The Stop hook with empty matcher fires after every conversation turn that triggers a stop, including simple questions. The reminder to update memory is noise for quick interactions.

---

## Inconsistencies

### INC-1: QA pair IDs use inconsistent naming

Some IDs are `test_001` through `test_010`, others are `test_0011` through `test_0030`. Mixed 3-digit and 4-digit zero-padding.

### INC-2: `scrape_infocom.py` doesn't use `.venv`

The script's docstring says `python scrape_infocom.py` but CLAUDE.md requires `.venv/Scripts/python.exe`. All scripts should document the venv path in their docstrings.

### INC-3: `embed_and_index.py` batch size differs from Colab

Local script uses `BATCH_SIZE = 8`, Colab notebook uses `BATCH_SIZE = 32`. This is intentional (CPU vs GPU) but not documented in either place.

---

## Performance

### PERF-1: `get_cached_embedding` does per-file I/O

Each cache lookup reads a separate `.npy` file from disk. For 1,390 sentence chunks, this means 1,390 `os.path.exists()` + potential `np.load()` calls. A single cache file (one large `.npy` with a JSON index) would be faster.

### PERF-2: `evaluate_retrieval.py` creates a new ChromaDB client per strategy

`evaluate_strategy()` creates `chromadb.PersistentClient()` each time it's called (line 104). Then `gemini_judge()` creates another one (line 186). Three separate client instantiations for the same DB in one run.

### PERF-3: `scrape_infocom.py` re-parses with html.parser

BeautifulSoup's `html.parser` is the slowest parser. Using `lxml` (if installed) would be 5-10x faster for parsing 65 HTML files.

---

## Missing Features / Robustness

### MISS-1: No retry logic for HTTP requests in scraper

`scrape_infocom.py` uses `resp.raise_for_status()` with no retry. A transient 503 or timeout will crash the entire run. httpx supports retries via `httpx.Client(transport=httpx.HTTPTransport(retries=3))`.

### MISS-2: No way to add new articles incrementally

The scraper always processes all pages. There's no `--new-only` flag to check for articles not yet in the cache. This means re-scraping the listing pages every time.

### MISS-3: No data validation between pipeline stages

Nothing verifies that:
- Chunk IDs in `chunks_*.json` match article IDs in `infocom_investigations.json`
- Embedding dimensions match expected 1024
- ChromaDB collection chunk count matches the JSON file

`load_embeddings.py` has a count check, but there's no end-to-end pipeline validation.

---

## Summary

| Category | Critical | Medium | Low |
|----------|----------|--------|-----|
| Bugs | 2 (BUG-1, BUG-2) | 2 (BUG-3, BUG-5) | 2 (BUG-4, BUG-6) |
| Security | 1 (SEC-1) | 1 (SEC-2) | 1 (SEC-3) |
| Duplication | 0 | 3 (DUP-1,2,3) | 0 |
| Design | 1 (DESIGN-5) | 3 (DESIGN-1,3,7) | 3 (DESIGN-2,4,6) |
| Hooks | 1 (HOOK-1) | 1 (HOOK-2) | 1 (HOOK-3) |
| Inconsistencies | 0 | 1 (INC-2) | 2 (INC-1, INC-3) |
| Performance | 0 | 1 (PERF-2) | 2 (PERF-1, PERF-3) |
| Missing | 0 | 2 (MISS-1, MISS-2) | 1 (MISS-3) |

**Top 5 to fix first:**
1. SEC-1: Check if API key was committed to git history, rotate if so
2. BUG-1: Fix exception type in `embed_and_index.py` delete_collection
3. BUG-2: Add batching to `evaluate_retrieval.py` embed_texts
4. DESIGN-5: Account for title prefix tokens in chunk token estimates
5. HOOK-1: Fix grep `-oP` portability for Windows
