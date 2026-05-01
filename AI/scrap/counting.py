import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://tabdeal.org"
START_URL = "https://tabdeal.org/help/"

visited = set()
to_visit = set([START_URL])

OUTPUT_FILE = "help_urls.txt"


def is_help_url(url: str):
    return url.startswith(BASE_URL + "/help") and "#" not in url


def extract_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for a in soup.find_all("a", href=True):
        url = urljoin(base_url, a["href"])
        if is_help_url(url):
            links.add(url)

    return links


def fetch_html(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return None


def crawl_urls():
    while to_visit:
        url = to_visit.pop()

        if url in visited:
            continue
        visited.add(url)

        print("🔎 Scanning:", url)

        html = fetch_html(url)
        if not html:
            print("❌ FAILED:", url)
            continue

        links = extract_links(html, url)
        to_visit.update(links - visited)

    return visited


if __name__ == "__main__":
    urls = crawl_urls()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for url in sorted(urls):
            f.write(url + "\n")

    print("\n🎉 DONE — Extracted", len(urls), "URLs")
    print("📁 Saved to:", OUTPUT_FILE)
