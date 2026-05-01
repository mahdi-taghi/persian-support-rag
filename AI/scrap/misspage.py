import requests
from bs4 import BeautifulSoup
import json
import asyncio
from playwright.async_api import async_playwright
from urllib.parse import urljoin

OUTPUT_FILE = "tabdeal_help.jsonl"
BASE_URL = "https://tabdeal.org"

# -----------------------------
# Utility Functions
# -----------------------------


def clean_text(text):
    return " ".join(text.split()).strip()


def extract_main_content(html):
    soup = BeautifulSoup(html, "html.parser")
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
            if len(text) > 50:
                return text

    return clean_text(soup.get_text(separator=" "))


def fetch_html_simple(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and len(r.text) > 200:
            return r.text
    except:
        pass
    return None


# -----------------------------
# Playwright fallback
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


async def robust_fetch(url):
    html = fetch_html_simple(url)
    if html and len(extract_main_content(html)) > 50:
        return html

    print("🔁 Falling back to Playwright:", url)
    return await fetch_with_playwright(url)


# -----------------------------
# Single-URL scrape function
# -----------------------------


async def scrape_single_page(url):
    print("📄 Fetching:", url)

    html = await robust_fetch(url)
    if not html:
        print("❌ Failed to fetch:", url)
        return

    content = extract_main_content(html)

    record = {
        "url": url,
        "content": content,
        "length": len(content),
    }

    # Append mode — add record to the existing dataset
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("✅ Added to", OUTPUT_FILE)


# -----------------------------
# Runner
# -----------------------------

if __name__ == "__main__":
    target = input("Enter URL to scrape: ").strip()
    asyncio.run(scrape_single_page(target))
