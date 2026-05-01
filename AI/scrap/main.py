import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import time
import asyncio
from playwright.async_api import async_playwright

BASE_URL = "https://tabdeal.org"
START_URL = "https://tabdeal.org/help/"

visited = set()
to_visit = set([START_URL])

OUTPUT_FILE = "tabdeal_help.jsonl"

# -----------------------------
# Helpers
# -----------------------------


def is_help_url(url):
    return url.startswith(BASE_URL + "/help")


def clean_text(text):
    return " ".join(text.split()).strip()


def extract_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        url = urljoin(base_url, a["href"])
        if is_help_url(url):
            links.add(url)
    return links


def extract_main_content(html):
    soup = BeautifulSoup(html, "html.parser")

    # Common selectors for help centers
    candidates = [
        "main",
        "article",
        ".help-content",
        ".post-content",
        ".content",
        ".entry-content",
        ".faq-item",
    ]

    for selector in candidates:
        node = soup.select_one(selector)
        if node:
            text = clean_text(node.get_text(separator=" "))
            if len(text) > 50:  # ensure it's real content
                return text

    # fallback to full text
    return clean_text(soup.get_text(separator=" "))


# -----------------------------
# Playwright Fallback Fetch
# -----------------------------


async def fetch_with_playwright(url):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(url, timeout=30000)
        await page.wait_for_timeout(1500)

        html = await page.content()

        await browser.close()
        return html


# -----------------------------
# Fetch HTML (Requests → Fallback)
# -----------------------------


def fetch_html(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and len(r.text) > 200:
            return r.text
    except:
        pass
    return None


async def robust_fetch(url):
    html = fetch_html(url)
    if html and len(extract_main_content(html)) > 50:
        return html

    print("🔁 Falling back to Playwright for:", url)
    return await fetch_with_playwright(url)


# -----------------------------
# Main Crawler
# -----------------------------


async def crawl():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        while to_visit:
            url = to_visit.pop()
            if url in visited:
                continue
            visited.add(url)

            print("📄 Fetching:", url)

            html = await robust_fetch(url)
            if not html:
                print("❌ Failed:", url)
                continue

            content = extract_main_content(html)
            links = extract_links(html, url)
            to_visit.update(links - visited)

            record = {
                "url": url,
                "content": content,
                "length": len(content),
            }

            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            time.sleep(0.5)

    print("🎉 Done! Output saved to:", OUTPUT_FILE)


# -----------------------------
# Run
# -----------------------------

asyncio.run(crawl())
