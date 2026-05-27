from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import trafilatura

from logic.counter import count_stats


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    return urlunparse((scheme, netloc, path, "", "", ""))


def is_same_domain(url: str, root_domain: str) -> bool:
    try:
        return urlparse(url).netloc.lower().endswith(root_domain.lower())
    except Exception:
        return False


def clean_text(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.replace("\u00a0", " ").split())


def extract_title_from_html(html: str, fallback: str = "") -> str:
    try:
        soup = BeautifulSoup(html, "html.parser")
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            if title:
                return title
    except Exception:
        pass
    return fallback


def extract_links_from_html(html: str, base_url: str, root_domain: str) -> list[str]:
    links = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href:
                continue
            absolute = urljoin(base_url, href)
            parsed = urlparse(absolute)

            if parsed.scheme not in ("http", "https"):
                continue
            if not is_same_domain(absolute, root_domain):
                continue

            links.append(normalize_url(absolute))
    except Exception:
        pass

    seen = set()
    out = []
    for item in links:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


async def crawl_site(root_url: str, max_pages: int = 100) -> list[dict]:
    root_url = normalize_url(root_url)
    root_domain = urlparse(root_url).netloc

    visited = set()
    queue = [root_url]
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 1200},
        )

        try:
            while queue and len(visited) < max_pages:
                current_url = normalize_url(queue.pop(0))

                if current_url in visited:
                    continue

                visited.add(current_url)

                try:
                    await page.goto(current_url, wait_until="networkidle", timeout=60000)
                    await page.wait_for_timeout(1500)
                    html = await page.content()

                    title = extract_title_from_html(html, fallback=current_url)

                    extracted = trafilatura.extract(
                        html,
                        include_comments=False,
                        include_tables=False,
                        include_links=False,
                        include_images=False,
                        output_format="txt",
                    )

                    if extracted:
                        text = clean_text(extracted)
                    else:
                        soup = BeautifulSoup(html, "html.parser")
                        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
                            tag.decompose()
                        text = clean_text(soup.get_text(separator=" ", strip=True))

                    stats = count_stats(text)

                    results.append(
                        {
                            "url": current_url,
                            "title": title,
                            "stats": stats,
                        }
                    )

                    links = extract_links_from_html(html, current_url, root_domain)
                    for link in links:
                        if link not in visited and link not in queue:
                            queue.append(link)

                except Exception as e:
                    results.append(
                        {
                            "url": current_url,
                            "title": "Fetch failed",
                            "stats": {
                                "count": 0,
                                "type": "words",
                                "language_group": f"Error: {str(e)}",
                            },
                        }
                    )

        finally:
            await browser.close()

    return results
