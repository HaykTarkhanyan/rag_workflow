"""
Scraper for Infocom.am investigation articles.
Crawls all paginated listing pages, extracts article URLs,
then scrapes each article with full metadata and content.

Features:
- Caches raw HTML per article in scraped_data/cache/ for fast reruns
- Skips already-cached articles unless --force is passed
- Saves final output to scraped_data/infocom_investigations.json
- Handles Armenian UTF-8 text on Windows console

Usage:
    python scrape_infocom.py            # normal run, uses cache
    python scrape_infocom.py --force    # re-download everything
    python scrape_infocom.py --parse    # re-parse cached HTML only (no network)
"""

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

# Fix Windows console encoding for Armenian text
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "https://infocom.am/category/indepth/investigation/"
OUTPUT_DIR = Path("scraped_data")
CACHE_DIR = OUTPUT_DIR / "cache"
URLS_CACHE = OUTPUT_DIR / "article_urls.json"
OUTPUT_FILE = OUTPUT_DIR / "infocom_investigations.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept-Language": "hy-AM,hy;q=0.9,en;q=0.8",
}

DELAY_BETWEEN_REQUESTS = 1.5  # seconds


def cache_path_for_url(url: str) -> Path:
    """Generate a cache file path for a URL."""
    url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
    # Extract the article ID from URL for readability
    match = re.search(r"infocom\.am/(\d+)/", url)
    article_id = match.group(1) if match else url_hash
    return CACHE_DIR / f"{article_id}_{url_hash}.html"


def get_total_pages(soup: BeautifulSoup) -> int:
    """Extract total page count from the archive title."""
    title = soup.find("title")
    if title:
        match = re.search(r"Page \d+ of (\d+)", title.text)
        if match:
            return int(match.group(1))
    page_links = soup.select('a[href*="/page/"]')
    max_page = 1
    for link in page_links:
        match = re.search(r"/page/(\d+)/", link.get("href", ""))
        if match:
            max_page = max(max_page, int(match.group(1)))
    return max_page


def extract_article_urls_from_listing(soup: BeautifulSoup) -> list[str]:
    """Extract article URLs from a category listing page."""
    urls = set()
    for h2 in soup.find_all("h2"):
        link = h2.find("a", href=True)
        if link and re.match(r"https://infocom\.am/\d+/", link["href"]):
            urls.add(link["href"])
    return sorted(urls)


def collect_all_article_urls(client: httpx.Client, force: bool = False) -> list[str]:
    """Crawl all listing pages and collect article URLs. Uses cache."""
    if not force and URLS_CACHE.exists():
        urls = json.loads(URLS_CACHE.read_text(encoding="utf-8"))
        print(f"Loaded {len(urls)} article URLs from cache ({URLS_CACHE})")
        return urls

    print("Fetching listing page 1...")
    resp = client.get(BASE_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    total_pages = get_total_pages(soup)
    print(f"Found {total_pages} pages of articles")

    all_urls = extract_article_urls_from_listing(soup)
    print(f"  Page 1: {len(all_urls)} articles")

    for page_num in range(2, total_pages + 1):
        time.sleep(DELAY_BETWEEN_REQUESTS)
        page_url = f"{BASE_URL}page/{page_num}/"
        print(f"Fetching listing page {page_num}...")
        resp = client.get(page_url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        page_urls = extract_article_urls_from_listing(soup)
        print(f"  Page {page_num}: {len(page_urls)} articles")
        all_urls.extend(page_urls)

    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    for url in all_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    # Cache the URL list
    URLS_CACHE.write_text(json.dumps(unique_urls, indent=2), encoding="utf-8")
    print(f"Cached {len(unique_urls)} URLs to {URLS_CACHE}")
    return unique_urls


def fetch_and_cache(client: httpx.Client, url: str, force: bool = False) -> str:
    """Fetch a URL and cache the raw HTML. Returns HTML string."""
    cache_file = cache_path_for_url(url)
    if not force and cache_file.exists():
        return cache_file.read_text(encoding="utf-8")

    resp = client.get(url)
    resp.raise_for_status()
    html = resp.text
    cache_file.write_text(html, encoding="utf-8")
    return html


def extract_json_ld(soup: BeautifulSoup) -> dict | None:
    """Extract JSON-LD structured data from the page."""
    script = soup.find("script", type="application/ld+json")
    if script:
        try:
            return json.loads(script.string)
        except (json.JSONDecodeError, TypeError):
            return None
    return None


def extract_article_content(soup: BeautifulSoup) -> str:
    """Extract the main article text content."""
    # Try single-container selectors first
    single_selectors = [
        ".elementor-widget-theme-post-content .elementor-widget-container",
        ".elementor-widget-theme-post-content",
        ".entry-content",
    ]
    for selector in single_selectors:
        el = soup.select_one(selector)
        if el:
            paragraphs = []
            for p in el.find_all(["p", "h2", "h3", "h4", "blockquote", "li"]):
                text = p.get_text(strip=True)
                if text:
                    paragraphs.append(text)
            if paragraphs:
                return "\n\n".join(paragraphs)

    # Infocom uses multiple .elementor-widget-text-editor blocks inside wp-post
    post_container = soup.select_one('[data-elementor-type="wp-post"]')
    if post_container:
        widgets = post_container.select(".elementor-widget-text-editor")
        if widgets:
            content_parts = []
            for widget in widgets:
                paragraphs = []
                for p in widget.find_all(["p", "h2", "h3", "h4", "blockquote", "li"]):
                    text = p.get_text(strip=True)
                    if text:
                        paragraphs.append(text)
                if paragraphs:
                    content_parts.append("\n\n".join(paragraphs))
            if content_parts:
                return "\n\n".join(content_parts)

    # Last fallback: any text-editor widget on the page
    content_parts = []
    for widget in soup.select(".elementor-widget-text-editor"):
        text = widget.get_text(separator="\n", strip=True)
        if text and len(text) > 50:
            content_parts.append(text)
    return "\n\n".join(content_parts) if content_parts else ""


def parse_article(html: str, url: str) -> dict:
    """Parse article HTML and extract all metadata + content."""
    soup = BeautifulSoup(html, "html.parser")
    article_data = {"url": url}

    # 1. OG meta tags
    og_fields = {
        "og:title": "title",
        "og:description": "description",
        "og:image": "image_url",
        "article:published_time": "published_at",
        "article:modified_time": "modified_at",
    }
    for prop, key in og_fields.items():
        meta = soup.find("meta", property=prop)
        if meta and meta.get("content"):
            article_data[key] = meta["content"]

    # 2. JSON-LD structured data (richest source)
    json_ld = extract_json_ld(soup)
    if json_ld and "@graph" in json_ld:
        for item in json_ld["@graph"]:
            item_type = item.get("@type", "")
            if item_type == "Article":
                article_data.setdefault("title", item.get("headline"))
                article_data.setdefault("published_at", item.get("datePublished"))
                article_data.setdefault("modified_at", item.get("dateModified"))
                article_data["word_count"] = item.get("wordCount")
                article_data["sections"] = item.get("articleSection", [])
                article_data["keywords"] = item.get("keywords", [])
                article_data["language"] = item.get("inLanguage")
                article_data["comment_count"] = item.get("commentCount")
            elif item_type == "Person":
                article_data["author"] = item.get("name")
                article_data["author_url"] = item.get("url")
                author_desc = item.get("description")
                if author_desc:
                    article_data["author_bio"] = author_desc

    # 3. Displayed date/time on page
    time_elements = soup.find_all("time")
    display_times = [t.get_text(strip=True) for t in time_elements if t.get_text(strip=True)]
    if display_times:
        article_data["display_date_parts"] = display_times

    # 4. Article body content
    article_data["content"] = extract_article_content(soup)

    # 5. Clean up title
    if "title" in article_data and article_data["title"]:
        article_data["title"] = re.sub(r"\s*-\s*Infocom\s*$", "", article_data["title"])

    article_data.setdefault("sections", [])
    return article_data


def main():
    parser = argparse.ArgumentParser(description="Scrape Infocom.am investigations")
    parser.add_argument("--force", action="store_true", help="Re-download everything, ignore cache")
    parser.add_argument("--parse", action="store_true", help="Re-parse cached HTML only, no network requests")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)

    if args.parse:
        # Parse-only mode: read from cache, no network
        if not URLS_CACHE.exists():
            print("ERROR: No cached URLs found. Run without --parse first.")
            sys.exit(1)
        article_urls = json.loads(URLS_CACHE.read_text(encoding="utf-8"))
        print(f"Parse-only mode: {len(article_urls)} URLs from cache")

        articles = []
        for i, url in enumerate(article_urls, 1):
            cache_file = cache_path_for_url(url)
            if not cache_file.exists():
                print(f"[{i}/{len(article_urls)}] SKIP (not cached): {url}")
                continue
            html = cache_file.read_text(encoding="utf-8")
            article = parse_article(html, url)
            articles.append(article)
            title = article.get("title", "No title")[:60]
            print(f"[{i}/{len(article_urls)}] Parsed: {title}")
    else:
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=30) as client:
            # Step 1: Collect URLs
            print("=" * 60)
            print("Step 1: Collecting article URLs")
            print("=" * 60)
            article_urls = collect_all_article_urls(client, force=args.force)
            print(f"Total unique articles: {len(article_urls)}")

            # Step 2: Fetch & parse each article
            print("\n" + "=" * 60)
            print("Step 2: Fetching & parsing articles")
            print("=" * 60)
            articles = []
            cached_count = 0
            fetched_count = 0

            for i, url in enumerate(article_urls, 1):
                cache_file = cache_path_for_url(url)
                is_cached = cache_file.exists() and not args.force

                try:
                    if is_cached:
                        html = cache_file.read_text(encoding="utf-8")
                        cached_count += 1
                        tag = "CACHE"
                    else:
                        html = fetch_and_cache(client, url, force=args.force)
                        fetched_count += 1
                        tag = "FETCH"
                        time.sleep(DELAY_BETWEEN_REQUESTS)

                    article = parse_article(html, url)
                    articles.append(article)
                    title = article.get("title", "No title")[:60]
                    content_len = len(article.get("content", ""))
                    print(f"[{i}/{len(article_urls)}] {tag}: {title} ({content_len} chars)")

                except Exception as e:
                    print(f"[{i}/{len(article_urls)}] ERROR: {url} - {e}")
                    articles.append({"url": url, "error": str(e)})

            print(f"\nFetched: {fetched_count}, From cache: {cached_count}")

    # Step 3: Save results
    print("\n" + "=" * 60)
    print("Step 3: Saving results")
    print("=" * 60)

    output = {
        "source": "infocom.am",
        "category": "investigation",
        "category_url": BASE_URL,
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_articles": len(articles),
        "articles": articles,
    }

    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(articles)} articles to {OUTPUT_FILE}")

    successful = [a for a in articles if "error" not in a]
    with_content = [a for a in successful if a.get("content")]
    failed = [a for a in articles if "error" in a]
    print(f"\nSummary: {len(successful)} succeeded ({len(with_content)} with content), {len(failed)} failed")
    if failed:
        print("Failed URLs:")
        for a in failed:
            print(f"  - {a['url']}: {a['error']}")


if __name__ == "__main__":
    main()
