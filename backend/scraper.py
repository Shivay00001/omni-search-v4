import httpx
from bs4 import BeautifulSoup
import asyncio

async def scrape_url(url: str, timeout: int = 10):
    """
    Fetches the content of a URL and extracts the main text using paragraph-aware chunking.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
            response = await client.get(url, timeout=timeout)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Remove script and style elements
                for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
                    script_or_style.decompose()
                
                # Extract text by paragraphs to preserve structure
                paragraphs = soup.find_all(['p', 'article', 'section'])
                if not paragraphs:
                    text = soup.get_text(separator="\n")
                else:
                    text = "\n\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 50])

                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                text = "\n".join(line for line in lines if line)
                
                # Industry-Grade Semantic Chunking (Simple Version)
                # Ensure we don't break mid-sentence if possible
                if len(text) > 6000:
                    # Find the last paragraph boundary before 6000
                    truncated = text[:6000]
                    last_newline = truncated.rfind('\n\n')
                    if last_newline > 3000:
                        text = truncated[:last_newline]
                    else:
                        text = truncated
                
                return text
    except Exception as e:
        print(f"Scraping error for {url}: {e}")
    return ""

async def scrape_multiple(urls: list[str]):
    """
    Scrapes multiple URLs concurrently.
    """
    tasks = [scrape_url(url) for url in urls]
    return await asyncio.gather(*tasks)

if __name__ == "__main__":
    # Test scraping
    test_url = "https://www.wikipedia.org/"
    res = asyncio.run(scrape_url(test_url))
    print(res[:500])
