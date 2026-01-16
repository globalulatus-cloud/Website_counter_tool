import asyncio
from typing import Set, List, Dict
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import httpx
from logic.counter import count_stats

async def crawl_site(start_url: str) -> List[Dict]:
    domain = urlparse(start_url).netloc
    to_visit = {start_url}
    visited = set()
    results = []
    
    # Semaphore to limit concurrency (prevent overwhelming target/self)
    semaphore = asyncio.Semaphore(5)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

    async with httpx.AsyncClient(follow_redirects=True, timeout=12.0, verify=False, headers=headers) as client:
        while to_visit:
            # Take a batch of URLs to process concurrently
            current_batch = list(to_visit)
            to_visit = set()
            
            tasks = []
            for url in current_batch:
                if url in visited:
                    continue
                visited.add(url)
                tasks.append(process_page(url, client, semaphore, domain))
            
            if not tasks:
                break
                
            batch_results = await asyncio.gather(*tasks)
            
            for page_res, found_links in batch_results:
                if page_res:
                    results.append(page_res)
                for link in found_links:
                    if link not in visited:
                        to_visit.add(link)
                
    return results

async def process_page(url: str, client: httpx.AsyncClient, semaphore: asyncio.Semaphore, domain: str):
    found_links = []
    page_data = None
    
    async with semaphore:
        try:
            response = await client.get(url)
            if response.status_code != 200 or 'text/html' not in response.headers.get('Content-Type', ''):
                return None, []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract stats
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
            
            text = soup.get_text(separator=' ')
            stats = count_stats(text)
            
            page_data = {
                "url": url,
                "stats": stats,
                "title": soup.title.string.strip() if soup.title and soup.title.string else url
            }
            
            # Find internal links
            for link in soup.find_all('a', href=True):
                full_url = urljoin(url, link['href'])
                parsed = urlparse(full_url)
                
                # Domain check and normalization
                if parsed.netloc == domain:
                    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    if clean_url.endswith('/'):
                        clean_url = clean_url[:-1]
                    found_links.append(clean_url)
                    
        except Exception as e:
            print(f"Error processing {url}: {e}")
            
    return page_data, found_links
