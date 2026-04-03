# Scraping Lessons

Mistakes, gotchas, and solutions discovered while building scrapers for this project.

---

## 1. Windows console encoding breaks Armenian text output

**Problem:** `print()` crashes with `'charmap' codec can't encode characters` when printing Armenian text on Windows. The default console encoding is `cp1252` which has no Armenian characters.

**Impact:** The entire scraper appeared to fail (65/65 articles showed as errors) even though the HTTP requests and parsing were successful. The error was in the `print()` inside a `try/except` block, which caught the encoding error and recorded it as a scraping failure.

**Fix:**
```python
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
```

**Lesson:** On Windows, always reconfigure stdout/stderr for UTF-8 at the top of any script that handles non-Latin text. Also, don't put `print()` and `scrape()` in the same try/except -- separate the I/O from the processing.

---

## 2. Same site, two different Elementor templates

**Problem:** Infocom.am uses two different article templates depending on article age:
- **Older articles (2023):** `[data-elementor-type="single-post"]` with `.elementor-widget-theme-post-content` (standard WP post content widget with `<p>` tags)
- **Newer articles (2024+):** `[data-elementor-type="wp-post"]` with multiple `.elementor-widget-text-editor` blocks

**Impact:** A selector that works for newer articles misses older ones entirely, and vice versa.

**Fix:** Try both templates in order. Check `single-post` + `theme-post-content` first (older), then fall back to `wp-post` + `text-editor` (newer).

**Lesson:** Always check articles from different time periods when building a scraper. CMS templates evolve over time and the same site may serve different HTML structures for old vs new content.

---

## 3. Elementor text-editor blocks without `<p>` tags

**Problem:** 31 out of 65 articles had zero `<p>` tags inside their content widgets. The text was stored as raw text nodes mixed with `<strong>`, `<em>`, and `<h2>` elements directly inside a `<div>`. Our initial extractor only looked for `p, h2, h3, h4, blockquote, li` elements.

**Impact:** Articles appeared to have content (because the `<h2>` and `<li>` tags were captured) but most of the body text was missing. Article 127773 went from 14,330 chars of actual content to only 1,402 chars extracted.

**Fix:** Created `_extract_from_element()` helper that:
1. Tries block-level tag extraction first (`p`, `h2`, `li`, etc.)
2. Checks if extracted text is >60% of the total `get_text()` output
3. Falls back to `get_text(separator="\n", strip=True)` if the block tags didn't capture enough

```python
def _extract_from_element(el) -> str:
    blocks = el.find_all(["p", "h2", "h3", "h4", "blockquote", "li"])
    if blocks:
        extracted = "\n\n".join(b.get_text(strip=True) for b in blocks if b.get_text(strip=True))
        full_text = el.get_text(strip=True)
        if len(extracted) > len(full_text) * 0.6:
            return extracted
    return el.get_text(separator="\n", strip=True)
```

**Lesson:** Never assume `<p>` tags exist. Elementor and similar page builders sometimes output raw text nodes without semantic HTML wrappers. Always have a `get_text()` fallback, and validate extraction quality by comparing against the total text length.

---

## 4. Fetch MCP raw HTML is mostly CSS on Elementor sites

**Problem:** When fetching Elementor-based pages with `raw=true`, the first 45,000+ characters were CSS/JS with no article content. The markdown mode stripped too much structure to see article URLs.

**Fix:** Used Playwright MCP's `browser_evaluate` to run JavaScript on the live page and extract article URLs and metadata directly from the DOM. This was far more efficient than parsing raw HTML.

**Lesson:** For Elementor/heavy-JS sites, use Playwright to extract structure (URLs, selectors) interactively, then use httpx+BeautifulSoup for the actual batch scraping. The Fetch MCP is great for quick content checks but struggles with heavy CMS pages.

---

## 5. Always cache raw HTML separately from parsed output

**Problem (avoided):** First version of the scraper had no caching. With 65 articles and 1.5s delay, a rerun would take ~2 minutes and hit the server again.

**Solution:** Cache raw HTML per article in `scraped_data/cache/{id}_{hash}.html`. The `--parse` flag re-extracts from cache without any network requests. The `--force` flag re-downloads everything.

**Lesson:** Separate fetching from parsing. Cache the raw response so you can iterate on parsing logic without re-fetching. This saved significant time when we needed to fix the content extraction twice.

---

## 6. JSON-LD structured data is the richest metadata source

**Discovery:** Infocom.am articles include JSON-LD `@graph` with `Article`, `Person`, `WebPage`, `BreadcrumbList`, and `Organization` objects. This gave us:
- Title, headline, datePublished, dateModified
- Author name, URL, and full bio
- Article sections, keywords, language, word count
- Image URL, thumbnail URL

This was more reliable and complete than parsing OG meta tags or scraping visible page elements.

**Lesson:** Always check for `<script type="application/ld+json">` first. Yoast SEO (and similar plugins) generate rich structured data that's easier to parse than the visual page.

---

## 7. BeautifulSoup `get_text(strip=True)` eats spaces between inline tags

**Problem:** HTML like `<em>word1 </em><em>word2</em>` produces `word1word2` when using `get_text(strip=True)`. Each text node is stripped individually, so the trailing space in `"word1 "` is removed before concatenation.

**Impact:** Words merged together throughout articles wherever the CMS split text across multiple `<em>`, `<span>`, or `<a>` tags. Common in Elementor-generated content.

**Fix:** Replace `el.get_text(strip=True)` with `" ".join(el.stripped_strings)`. This preserves word boundaries because each stripped text node becomes a separate string that gets joined with a space.

```python
# BAD: eats spaces between <em>word1 </em><em>word2</em>
text = el.get_text(strip=True)  # -> "word1word2"

# GOOD: preserves word boundaries
text = " ".join(el.stripped_strings)  # -> "word1 word2"
```

**Lesson:** Never use `get_text(strip=True)` for content extraction. Always use `" ".join(el.stripped_strings)` when word boundaries matter. This is a well-known BeautifulSoup gotcha but easy to forget.

---


1. **Explore** the site with Fetch MCP (markdown mode) to understand the content
2. **Inspect** with Playwright MCP to find article URLs and HTML structure
3. **Build** the scraper with httpx + BeautifulSoup, caching raw HTML
4. **Test** on a few articles, check content length distribution
5. **Cross-check** scraped output against live page to verify completeness
6. **Iterate** on parsing using `--parse` flag (no network needed)
