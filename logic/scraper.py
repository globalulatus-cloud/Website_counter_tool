import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import trafilatura


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


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


async def fetch_rendered_html(url: str, timeout_ms: int = 60000) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1440, "height": 1200},
            )
            await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            await page.wait_for_timeout(1500)
            return await page.content()
        finally:
            await browser.close()


async def fetch_website_text(url: str) -> tuple[str, str, str]:
    html = await fetch_rendered_html(url)
    title = extract_title_from_html(html, fallback=url)

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

    return text, title, html
