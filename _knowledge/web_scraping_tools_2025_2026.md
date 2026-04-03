# Web Scraping Libraries & Tools for RAG Pipelines (2025-2026)

Research compiled: April 2026

---

## 1. Python Libraries (Traditional)

### BeautifulSoup
- **Language:** Python
- **Package:** `beautifulsoup4` (pip/uv)
- **GitHub:** https://code.launchpad.net/beautifulsoup (also mirrored on PyPI)
- **Key Features:**
  - HTML/XML parser that creates a navigable tree structure
  - 10M+ weekly downloads; the most widely used parsing library
  - Lightweight, beginner-friendly, extensive documentation
  - Works with multiple parsers (lxml, html.parser, html5lib)
- **Best Use Case:** Parsing static HTML pages; quick prototyping
- **RAG/LLM Fit:** Low -- outputs raw parsed data, no markdown/LLM-ready output. You need to build your own cleaning pipeline. Good as a building block inside a larger pipeline.

### Scrapy
- **Language:** Python
- **Package:** `scrapy`
- **GitHub:** https://github.com/scrapy/scrapy
- **Key Features:**
  - Full-featured crawling framework (not just a library)
  - Built-in request scheduling, middleware, pipelines, and export
  - Async architecture for high throughput
  - v2.14.0 (Jan 2026) introduced more coroutine-based APIs
- **Best Use Case:** Large-scale structured crawling (thousands to millions of pages)
- **RAG/LLM Fit:** Medium -- excellent for bulk collection, but you need post-processing to convert to LLM-friendly formats. Can be combined with LLM extraction in pipelines.

### Playwright (Python)
- **Language:** Python (also JS/TS)
- **Package:** `playwright`
- **GitHub:** https://github.com/microsoft/playwright-python
- **Key Features:**
  - Microsoft-backed; supports Chromium, Firefox, WebKit from one API
  - Handles JavaScript-heavy SPAs, dynamic content, shadow DOM
  - Auto-wait, network interception, multi-page scenarios
  - Default choice for browser automation in 2026
- **Best Use Case:** Scraping JS-rendered pages, SPAs, sites with anti-bot protections
- **RAG/LLM Fit:** High -- foundational layer used by Crawl4AI, llm-scraper, Stagehand, and most modern AI scraping tools.

### Selenium
- **Language:** Python (also Java, JS, C#, Ruby)
- **Package:** `selenium`
- **GitHub:** https://github.com/SeleniumHQ/selenium
- **Key Features:**
  - Broadest browser support and legacy compatibility
  - Mature ecosystem, huge community
  - Slower than Playwright, more flaky scripts
- **Best Use Case:** Legacy projects; cross-browser testing scenarios
- **RAG/LLM Fit:** Medium -- works but Playwright is preferred for new projects.

### httpx
- **Language:** Python
- **Package:** `httpx`
- **GitHub:** https://github.com/encode/httpx
- **Key Features:**
  - Modern async HTTP client (requests-compatible API)
  - HTTP/2 support, connection pooling
  - Async/await native
- **Best Use Case:** Fast HTTP requests for static pages, API scraping
- **RAG/LLM Fit:** Low on its own -- good as the HTTP layer in a larger pipeline.

### Scrapling (Emerging Star)
- **Language:** Python
- **Package:** `scrapling`
- **GitHub:** https://github.com/D4Vinci/Scrapling
- **Stars:** 20K+ (fast-growing)
- **Key Features:**
  - **Adaptive parsing** -- learns from website changes, auto-relocates elements when HTML structure changes
  - Built-in anti-bot bypass (Cloudflare Turnstile out of the box)
  - Spider framework with pause/resume, proxy rotation
  - Interactive IPython scraping shell
  - 92% test coverage, full type hints
  - 10x faster JSON serialization than stdlib
- **Best Use Case:** Scraping sites that frequently change structure; anti-bot evasion
- **RAG/LLM Fit:** Medium-High -- adaptive parsing reduces maintenance burden. No native LLM integration, but pairs well with LLM extraction.

---

## 2. JavaScript/Node Libraries

### Playwright (Node.js)
- **Language:** JavaScript/TypeScript
- **Package:** `playwright`
- **GitHub:** https://github.com/microsoft/playwright
- **Key Features:** Same as Python version; TypeScript-native, faster execution
- **Best Use Case:** JS-heavy scraping, browser automation
- **RAG/LLM Fit:** High -- used as foundation by Crawlee, Stagehand, llm-scraper.

### Puppeteer
- **Language:** JavaScript/TypeScript
- **Package:** `puppeteer`
- **GitHub:** https://github.com/puppeteer/puppeteer
- **Key Features:**
  - Google-maintained; Chrome/Chromium only
  - Mature, well-documented
  - Being gradually superseded by Playwright for new projects
- **Best Use Case:** Chrome-specific automation, PDF generation
- **RAG/LLM Fit:** Medium -- works but Playwright is more versatile.

### Cheerio
- **Language:** JavaScript/TypeScript
- **Package:** `cheerio`
- **GitHub:** https://github.com/cheeriojs/cheerio
- **Key Features:**
  - jQuery-like API for parsing static HTML (server-side)
  - Extremely fast, low memory footprint
  - No browser needed
- **Best Use Case:** Parsing static HTML in Node.js pipelines
- **RAG/LLM Fit:** Low -- parsing only, no rendering or LLM integration.

### Crawlee
- **Language:** JavaScript/TypeScript (also Python)
- **Package:** `crawlee` (npm) / `crawlee` (pip)
- **GitHub:** https://github.com/apify/crawlee
- **Key Features:**
  - Built by Apify; wraps Playwright, Puppeteer, Cheerio, and raw HTTP
  - Error handling, request queues, storage, proxy rotation, fingerprinting out of the box
  - Switch between HTTP and browser crawlers seamlessly
  - Python version available (uses Playwright)
  - Designed to work with Apify cloud platform
- **Best Use Case:** Production-grade crawlers that need reliability at scale
- **RAG/LLM Fit:** High -- battle-tested infrastructure for data pipelines. Integrates with Apify's AI extraction features.

### llm-scraper
- **Language:** TypeScript
- **Package:** `llm-scraper` (npm)
- **GitHub:** https://github.com/mishushakov/llm-scraper
- **Key Features:**
  - Turns any webpage into structured data using LLMs
  - Type-safe schemas with Zod or JSON Schema
  - Built on Playwright for rendering
  - Supports OpenAI, Anthropic, Google, Llama, Qwen
  - Streaming support for large extractions
  - Validates LLM outputs against schemas
- **Best Use Case:** Extracting structured JSON data from any page without writing selectors
- **RAG/LLM Fit:** Very High -- purpose-built for LLM workflows. Define a schema, get typed data.

---

## 3. AI-Powered Scraping Tools

### Crawl4AI
- **Language:** Python
- **Package:** `crawl4ai` (pip/uv)
- **GitHub:** https://github.com/unclecode/crawl4ai
- **Stars:** 50K+
- **Key Features:**
  - Converts web pages to clean, LLM-ready Markdown
  - Heuristic-based noise filtering (removes ads, nav, boilerplate)
  - LLM-based structured extraction (supports all major LLMs)
  - Chunking strategies: topic-based, regex, sentence-level
  - CSS/XPath selectors + LLM extraction hybrid
  - Shadow DOM flattening, anti-bot detection
  - Self-hostable, fully open-source
  - 100% extraction accuracy with GPT-4o on benchmarks
  - v0.8.x with advanced pattern-learning algorithms
- **Best Use Case:** Building RAG knowledge bases from web content; agent data pipelines
- **RAG/LLM Fit:** **Excellent** -- purpose-built for RAG. Outputs clean Markdown optimized for LLM token efficiency. The top open-source choice for RAG ingestion.

### Firecrawl
- **Language:** Python SDK, Node SDK, REST API
- **Package:** `firecrawl-py` (pip) / `@mendable/firecrawl-js` (npm)
- **GitHub:** https://github.com/firecrawl/firecrawl (formerly mendableai/firecrawl)
- **Stars:** 48K+
- **Key Features:**
  - Converts any URL to clean Markdown in one API call
  - `/extract` endpoint with JSON schema for structured extraction (uses GPT-4o)
  - Full site crawling: follows links, respects robots.txt/sitemaps, handles pagination
  - Can crawl 10,000+ page sites with a single API call
  - 6.8% noise ratio, 89% recall at retrieval depth 5
  - Y Combinator backed, $14.5M Series A, 350K+ developers
  - Self-hostable or cloud API
- **Pricing:** Free tier available; from $19/month (500 credits) to enterprise
- **Best Use Case:** Production RAG pipelines needing reliable, clean Markdown at scale
- **RAG/LLM Fit:** **Excellent** -- the leading commercial solution for AI web extraction. Clean Markdown output with minimal noise.

### ScrapeGraphAI
- **Language:** Python
- **Package:** `scrapegraphai` (pip/uv)
- **GitHub:** https://github.com/VinciGit00/Scrapegraphai
- **Key Features:**
  - Natural language prompts to define what to extract
  - Schema-validated JSON output
  - Uses LLMs (GPT-4, Claude, Gemini, local models via Ollama) to understand page structure
  - Graph-based pipeline architecture
  - Multiple scraping strategies (SmartScraper, SearchScraper, etc.)
  - Per-page focused extraction (not recursive crawling)
- **Pricing:** From $19/month for 5,000 credits
- **Best Use Case:** Extracting structured data from variable-layout pages using natural language
- **RAG/LLM Fit:** High -- great for structured entity extraction. Less suited for bulk Markdown ingestion (use Firecrawl/Crawl4AI for that).

### Browser-Use
- **Language:** Python (requires Python >= 3.11)
- **Package:** `browser-use` (pip/uv: `uv add browser-use`)
- **GitHub:** https://github.com/browser-use/browser-use
- **Stars:** 50K+
- **Key Features:**
  - Makes websites accessible to AI agents
  - AI agent controls the browser via natural language
  - Built on Playwright
  - Supports multi-step web workflows (click, type, navigate, extract)
  - Works with OpenAI, Anthropic, and other LLM providers
- **Best Use Case:** AI agents that need to browse, interact, and extract from the web autonomously
- **RAG/LLM Fit:** High -- ideal for agentic RAG where the agent decides what to scrape. Overkill for bulk static scraping.

### Jina Reader API
- **Language:** REST API (language-agnostic) + ReaderLM-v2 model
- **API:** `https://r.jina.ai/{url}` -- just prepend to any URL
- **GitHub:** https://github.com/jina-ai/reader
- **Model:** https://huggingface.co/jinaai/ReaderLM-v2 (1.5B params)
- **Key Features:**
  - Zero-setup: prepend `r.jina.ai/` to any URL for LLM-friendly text
  - ReaderLM-v2: 1.5B param model for HTML-to-Markdown, supports 512K token documents
  - 29 language support, 20% higher accuracy than v1
  - HTML-to-JSON extraction mode
  - Free tier available
- **Best Use Case:** Quick prototyping of RAG pipelines; zero-setup content extraction
- **RAG/LLM Fit:** **Excellent** -- literally built for RAG. Zero friction. Start here for prototyping, move to Firecrawl/Crawl4AI for production.

### Spider
- **Language:** Rust core, Python/Node SDKs, REST API
- **Package:** `spider-client` (pip)
- **GitHub:** https://github.com/spider-rs/spider
- **API:** https://spider.cloud
- **Key Features:**
  - Rust engine: 7x throughput vs Firecrawl, 9.5x vs Crawl4AI
  - 74 pages/second average, 500-page crawl in under 20 seconds
  - 91.5% recall, 4.2% noise ratio
  - Proxy rotation, anti-bot bypass, browser rendering, markdown conversion
  - Pay-as-you-go: ~$0.48/1K pages (bandwidth + compute based)
  - No subscription, no credit expiration
  - LangChain integration available
- **Best Use Case:** High-volume, speed-critical crawling for RAG at scale
- **RAG/LLM Fit:** **Excellent** -- fastest option for bulk ingestion. Best price-performance ratio.

---

## 4. Headless Browser Services / Scraping Platforms

### Browserbase
- **Language:** Cloud API; JS/Python SDKs
- **Website:** https://www.browserbase.com
- **Key Features:**
  - Managed headless Chromium instances in the cloud
  - Session persistence, debugging tools
  - Full Playwright/Puppeteer compatibility
  - Creators of Stagehand (AI automation framework)
- **Pricing:** From ~$50/month, scales with browser-hours consumed
- **Best Use Case:** Teams needing managed browser infrastructure without server ops
- **RAG/LLM Fit:** High -- provides the infrastructure layer for AI scraping tools.

### Stagehand (by Browserbase)
- **Language:** TypeScript (Python SDK also available)
- **GitHub:** https://github.com/browserbase/stagehand (also: https://github.com/browserbase/stagehand-python)
- **Stars:** 50K+
- **Key Features:**
  - AI-native browser automation: mix code precision with natural language flexibility
  - Self-healing: auto-caches actions, re-invokes AI when site structure changes
  - Computer-use model integration (OpenAI, Anthropic) with one line of code
  - v3: 44% faster, iframe/shadow-root support
  - Multiple LLM provider support
- **Best Use Case:** Building AI agents that interact with websites; adaptive scraping
- **RAG/LLM Fit:** Very High -- bridges traditional automation with AI adaptability.

### Apify
- **Language:** Cloud platform; JS/Python SDKs
- **Website:** https://apify.com
- **GitHub:** https://github.com/apify/crawlee
- **Key Features:**
  - Full scraping cloud with Crawlee integration
  - Apify Store: pre-built scrapers for Amazon, LinkedIn, Instagram, Google Maps, etc.
  - AI extraction features with LLM integration
  - Integrated proxy system, automatic rate limiting
  - Serverless actor model for scalable execution
- **Pricing:** From $49/month; 14-day free trial
- **Best Use Case:** Production scraping at scale without managing infrastructure
- **RAG/LLM Fit:** High -- pre-built actors + AI extraction = fast pipeline setup.

### ScrapingBee
- **Language:** REST API; SDKs for Python, Node, Ruby, Go, Java
- **Website:** https://www.scrapingbee.com
- **Key Features:**
  - Simple HTTP API that handles proxies + headless Chrome
  - Auto-adjusts concurrency/rate limits to avoid blocks
  - JavaScript rendering option
  - Screenshot API
- **Pricing:** 1K free credits; from $49/month
- **Best Use Case:** Simple API-based scraping without managing browsers or proxies
- **RAG/LLM Fit:** Medium -- good infrastructure layer, no native LLM features.

### Bright Data
- **Language:** Cloud platform; multiple SDKs
- **Website:** https://brightdata.com
- **Key Features:**
  - Largest proxy network in the industry
  - Web Scraper IDE, pre-built datasets
  - AI-powered extraction with structured output
  - No-code scraping interface
- **Best Use Case:** Enterprise-scale data collection with proxy infrastructure
- **RAG/LLM Fit:** Medium-High -- AI extraction features, but primarily a proxy/infrastructure provider.

---

## 5. LLM-Integrated Scraping (Tools Combining LLMs with Extraction)

### Tier 1: Purpose-Built for RAG/LLM Workflows

| Tool | Type | LLM Integration | Output Format | Best For |
|------|------|-----------------|---------------|----------|
| **Crawl4AI** | Open-source Python | All major LLMs | Clean Markdown, structured JSON | Self-hosted RAG pipelines |
| **Firecrawl** | API + self-host | GPT-4o extraction | Markdown, HTML, JSON | Production RAG at scale |
| **Jina Reader** | API + model | ReaderLM-v2 (1.5B) | Markdown, JSON | Zero-setup prototyping |
| **Spider** | API + self-host | LLM extraction included | Markdown, JSON, HTML | High-throughput bulk ingestion |

### Tier 2: Structured Extraction Focus

| Tool | Type | LLM Integration | Output Format | Best For |
|------|------|-----------------|---------------|----------|
| **ScrapeGraphAI** | Python library | GPT-4, Claude, Gemini, Ollama | Schema-validated JSON | Structured entity extraction |
| **llm-scraper** | TypeScript library | OpenAI, Anthropic, Google | Zod-typed JSON | Type-safe extraction in TS |
| **Instructor** | Python/TS library | All major LLMs | Pydantic/Zod models | Schema extraction from any text |

### Tier 3: Agentic Web Browsing

| Tool | Type | LLM Integration | Output Format | Best For |
|------|------|-----------------|---------------|----------|
| **Browser-Use** | Python library | OpenAI, Anthropic | Flexible | AI agents browsing autonomously |
| **Stagehand** | TypeScript (+Python) | OpenAI, Anthropic, Google | Flexible | Self-healing browser automation |
| **Skyvern** | Python | Multiple LLMs | Structured | Form filling, workflow automation |

---

## 6. Recommended Stacks for RAG Pipelines

### Prototyping / Small Scale
```
Jina Reader API (r.jina.ai/) --> chunk --> embed --> vector store
```
Zero setup, free tier, instant Markdown output.

### Production / Medium Scale
```
Crawl4AI or Firecrawl --> chunking (topic/sentence) --> embed --> vector store
```
- **Crawl4AI** if self-hosting and cost control matter
- **Firecrawl** if you want a managed API with higher reliability

### High-Volume / Speed-Critical
```
Spider API --> Markdown output --> chunk --> embed --> vector store
```
Best throughput and price-performance at scale.

### Structured Data Extraction
```
ScrapeGraphAI or llm-scraper --> schema-validated JSON --> store/index
```
When you need typed, structured entities rather than raw text.

### Agentic / Dynamic
```
Browser-Use or Stagehand --> AI agent navigates + extracts --> process --> store
```
When the scraping target requires interaction (login, search, pagination decisions).

---

## 7. Key Benchmarks (2026)

From independent benchmarks:
- **Spider**: 74 pages/sec, 91.5% recall, 4.2% noise, ~$0.48/1K pages
- **Firecrawl**: ~10 pages/sec, 89% recall, 6.8% noise, ~$0.83/1K pages
- **Crawl4AI**: ~8 pages/sec, 100% accuracy on structured extraction (with GPT-4o), free (self-hosted)
- **Flat JSON** gives LLMs best extraction accuracy (F1 = 0.9567) vs raw HTML
- **Clean Markdown** is optimal for RAG (preserves structure, token-efficient)

---

## Sources

- https://github.com/unclecode/crawl4ai
- https://github.com/firecrawl/firecrawl
- https://github.com/VinciGit00/Scrapegraphai
- https://github.com/browser-use/browser-use
- https://github.com/D4Vinci/Scrapling
- https://github.com/apify/crawlee
- https://github.com/mishushakov/llm-scraper
- https://github.com/jina-ai/reader
- https://github.com/spider-rs/spider
- https://github.com/browserbase/stagehand
- https://spider.cloud/blog/firecrawl-vs-crawl4ai-vs-spider-honest-benchmark
- https://www.morphllm.com/ai-web-scraping
- https://www.firecrawl.dev/blog/best-web-extraction-tools
- https://scrapeops.io/web-scraping-playbook/best-ai-web-scraping-tools/
