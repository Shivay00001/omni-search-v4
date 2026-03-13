import asyncio
import httpx
from bs4 import BeautifulSoup
from translator_manager import translator_manager
from urllib.parse import unquote, urlparse, parse_qs
import time

# Industry-Grade Search Cache (In-Memory)
_search_cache = {}

def clean_ddg_url(url: str) -> str:
    """Extracts the actual URL from DuckDuckGo's redirection link."""
    if "uddg=" in url:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        if "uddg" in query_params:
            return unquote(query_params["uddg"][0])
    return url

async def search_single(query: str, max_results: int = 5):
    """
    Worker to perform a manual resilient DDG search.
    Bypasses library blocks using custom headers and direct HTML parsing.
    """
    results = []
    url = "https://duckduckgo.com/html/"
    params = {"q": query}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://duckduckgo.com/",
        "DNT": "1"
    }
    
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                # DDG 'html' interface uses specific classes for results
                result_blocks = soup.find_all('div', class_='result')
                for block in result_blocks[:max_results]:
                    title_tag = block.find('a', class_='result__a')
                    snippet_tag = block.find('a', class_='result__snippet')
                    if title_tag:
                        raw_url = title_tag['href']
                        clean_url = clean_ddg_url(raw_url)
                        results.append({
                            "title": title_tag.get_text().strip(),
                            "url": clean_url,
                            "snippet": snippet_tag.get_text().strip() if snippet_tag else ""
                        })
            else:
                print(f"Manual Search Blocked: {response.status_code}")
    except Exception as e:
        print(f"Manual search error for '{query}': {e}")
    return results

async def apply_rl_feedback(results: list):
    """
    Applies Reinforcement Learning feedback to adjust result scores.
    Boosts/Buries results based on domain reputation in the rl_feedback table.
    """
    try:
        from database import AsyncSessionLocal
        from models import RL_Feedback
        from sqlalchemy import select, func
        
        async with AsyncSessionLocal() as session:
            # Aggregate feedback scores by domain
            stmt = select(RL_Feedback.domain, func.sum(RL_Feedback.score)).group_by(RL_Feedback.domain)
            feedback_result = await session.execute(stmt)
            feedback_map = {row[0]: row[1] for row in feedback_result.all()}
            
            for res in results:
                domain = urlparse(res["url"]).netloc
                boost = feedback_map.get(domain, 0.0)
                res["score"] = res.get("score", 0.0) + (boost * 2.0) # Weight RL feedback
    except Exception as e:
        print(f"RL Feedback application failed: {e}")
    return results

def rerank_results(query: str, results: list, top_k: int = 5):
    """
    Reranks results based on simple keyword density (The Moat).
    """
    keywords = set(query.lower().split())
    for res in results:
        text = (res["title"] + " " + res["snippet"]).lower()
        score = sum(1 for kw in keywords if kw in text)
        res["score"] = score
        
    return results # Return all for further processing (RL)

async def search_web(query: str, max_results: int = 5, multilingual: bool = True):
    """
    Industry-Grade Search:
    1. Check Cache
    2. Translates query to English (Global Data).
    3. Performs parallel manual searches.
    4. Deduplicates, Reranks, and merges results.
    """
    cache_key = f"{query}_{multilingual}_{max_results}"
    if cache_key in _search_cache:
        cached_val, timestamp = _search_cache[cache_key]
        if time.time() - timestamp < 3600: # 1 hour cache
            print(f"Cache hit for search: {query}")
            return cached_val

    queries = [query]
    
    if multilingual:
        # Translate to English for global reach
        en_query = await translator_manager.translate_to_en(query)
        if en_query.lower() != query.lower():
            queries.append(en_query)
            
    # Parallel search tasks
    tasks = [search_single(q, max_results=max_results) for q in queries]
    search_responses = await asyncio.gather(*tasks)
    
    # Flatten and Deduplicate by URL
    all_results = []
    seen_urls = set()
    
    for resp in search_responses:
        for item in resp:
            if item["url"] not in seen_urls:
                all_results.append(item)
                seen_urls.add(item["url"])
                
    print(f"Manual search found {len(all_results)} raw results.")
    
    # Reranking
    all_results = rerank_results(query, all_results)
    
    # RL Feedback Layer
    all_results = await apply_rl_feedback(all_results)
    
    # Final Sort
    final_results = sorted(all_results, key=lambda x: x["score"], reverse=True)[:max_results * 2]
    
    # Store in cache
    _search_cache[cache_key] = (final_results, time.time())
    
    return final_results

if __name__ == "__main__":
    # Test the search
    test_query = "Latest nuclear fusion breakthroughs"
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(search_web(test_query))
    import json
    print(json.dumps(res, indent=2))
