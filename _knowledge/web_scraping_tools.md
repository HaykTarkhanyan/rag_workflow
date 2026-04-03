# Web Scraping Tools & MCP Servers for RAG Workflows

Reference guide for web scraping libraries, Claude Code MCP servers, and skills relevant to RAG data ingestion.

## MCP Servers for Claude Code

### Browser Automation

| Name | Install Command | Cost | Best For |
|------|----------------|------|----------|
| **Playwright MCP** (Microsoft) | `claude mcp add playwright -- npx @playwright/mcp@latest` | Free | General browser automation, most popular (~8.7M downloads) |
| **Chrome DevTools MCP** (Google) | `claude mcp add chrome-devtools --scope user -- npx chrome-devtools-mcp@latest` | Free | Debugging, network inspection, performance |
| **Browser MCP** (browsermcp.io) | Chrome extension + MCP config | Free | Uses real browser with existing sessions/cookies |
| **Browserbase MCP** | `claude mcp add --transport http browserbase "https://mcp.browserbase.com/mcp?browserbaseApiKey=KEY"` | Paid | Cloud-hosted browser, no local Chrome needed |
| **Hyperbrowser MCP** | `npx -y @smithery/cli install @hyperbrowserai/mcp --client claude` | Paid | Cloud browser + structured extraction + Bing search |

### Web Scraping / Crawling

| Name | Install Command | Cost | Best For |
|------|----------------|------|----------|
| **Firecrawl MCP** | `claude mcp add firecrawl-mcp -- env FIRECRAWL_API_KEY=fc-KEY npx -y firecrawl-mcp` | Free tier (10 scrapes/min) | Production scraping, anti-bot, clean markdown output |
| **Jina AI MCP** | `claude mcp add -s user --transport http jina https://mcp.jina.ai/v1 --header "Authorization: Bearer ${JINA_API_KEY}"` | Free tier | Quick URL-to-markdown, academic search, embeddings |
| **Crawl4AI MCP** (Docker) | Docker config (see below) | Free, self-hosted | Free alternative to Firecrawl, JS rendering |
| **Apify MCP** | `npx @apify/actors-mcp-server` | Free tier | Thousands of pre-built scrapers (Amazon, LinkedIn, etc.) |
| **MCP Fetch** (Anthropic) | `claude mcp add fetch -- uvx mcp-server-fetch` | Free | Basic HTTP fetch + HTML-to-markdown, no JS rendering |
| **Spider Cloud MCP** | GitHub: willbohn/spider-mcp | Paid | Fastest option (74 pages/sec), Rust engine |

### Crawl4AI Docker Config

```json
{
  "mcpServers": {
    "crawl4ai-mcp": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "--volume", "/tmp/crawl4ai-crawls:/app/crawls", "uysalsadi/crawl4ai-mcp-server:latest"]
    }
  }
}
```

## Claude Code Skills (No MCP, Markdown-Based)

| Name | GitHub | Features |
|------|--------|----------|
| **Crawl4AI Skill** | brettdavies/crawl4ai-skill | JS support, CSS/LLM extraction, markdown output, batch |
| **Scrapling Skill** | Cedriccmh/claude-code-skill-scrapling | Auto-selects fetcher, Cloudflare bypass, session auth |
| **Web Scraper Skill** | yfe404/web-scraper | Adaptive multi-phase: curl first, escalates to browser |
| **Firecrawl Plugin** | firecrawl/firecrawl-claude-plugin | Firecrawl as CLI skill, search/scrape/crawl |

## Python Scraping Libraries

### Traditional

| Library | Stars | Best For | Notes |
|---------|-------|----------|-------|
| **BeautifulSoup** | Mature | Static HTML parsing | Lightweight, no JS, building block |
| **Scrapy** | 55K+ | Large-scale crawling (millions of pages) | Async, middleware, pipelines |
| **Playwright** (Python) | 50K+ | Browser automation | Chromium/Firefox/WebKit, foundation for AI tools |
| **Selenium** | Mature | Legacy browser automation | Superseded by Playwright for new projects |
| **httpx** | 15K+ | Async HTTP requests | HTTP/2, fast for static pages and APIs |
| **Scrapling** | 20K+ | Adaptive parsing with auto-relocate | Cloudflare bypass, learns from site changes |

### AI-Powered (Best for RAG)

| Tool | Stars | Output | Cost | Key Feature |
|------|-------|--------|------|-------------|
| **Crawl4AI** | 50K+ | Clean markdown + JSON | Free (self-host) | Best open-source RAG ingestion, chunking strategies |
| **Firecrawl** | 48K+ | Markdown + structured JSON | Free tier / $19+/mo | YC-backed, anti-bot, `/extract` for structured data |
| **ScrapeGraphAI** | 20K+ | Schema-validated JSON | Depends on LLM | Natural language prompts define extraction |
| **Browser-Use** | 50K+ | Varies | Free | AI agent controls browser via natural language |
| **Jina Reader** | 10K+ | Markdown | Free tier | Zero-setup: prepend `r.jina.ai/` to any URL |
| **Spider** | 15K+ | Markdown | ~$0.48/1K pages | Rust engine, 74 pages/sec, fastest option |
| **Stagehand** | 50K+ | Varies | From ~$50/mo | AI-native browser, self-healing, by Browserbase |

## Recommended Stack for RAG Ingestion

### Tier 1: Install Now (Free, High Impact)

1. **Playwright MCP** -- Browser automation foundation, zero cost
2. **MCP Fetch** -- Quick page grabs without browser overhead
3. **Crawl4AI** (Python library) -- Best free tool for converting web pages to RAG-ready markdown

### Tier 2: Add When Needed

4. **Firecrawl MCP** -- When you need anti-bot bypass or batch crawling (free tier available)
5. **Jina AI MCP** -- Quick URL-to-markdown + academic paper search
6. **Scrapling** -- When hitting Cloudflare-protected sites

### Tier 3: Scale

7. **Apify MCP** -- Pre-built scrapers for specific platforms
8. **Spider** -- High-volume crawling (74 pages/sec)
9. **Browserbase** -- Cloud browsers for heavy automation

## Key Insights

- **Clean markdown is optimal for RAG** -- preserves structure, token-efficient
- **68% of production scraping uses 2+ tools** -- start simple, escalate as needed
- **Crawl4AI + Firecrawl** cover ~90% of RAG scraping needs
- **Playwright MCP** is the most popular MCP server (~8.7M npm downloads)
- For Armenian web content: Jina Reader supports 29 languages via ReaderLM-v2

## GitHub References

- Playwright MCP: https://github.com/microsoft/playwright-mcp
- Firecrawl: https://github.com/firecrawl/firecrawl
- Crawl4AI: https://github.com/unclecode/crawl4ai
- Jina AI MCP: https://github.com/jina-ai/MCP
- Browser-Use: https://github.com/browser-use/browser-use
- Scrapling: https://github.com/D4Vinci/Scrapling
- ScrapeGraphAI: https://github.com/VinciGit00/Scrapegraphai
- Stagehand: https://github.com/browserbase/stagehand
- Apify MCP: https://github.com/apify/apify-mcp-server
