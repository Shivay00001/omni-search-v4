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
                            "snippet": snippet_tag.get_text().strip() if snippet_tag else "",
                            "provider": "ddg_html",
                        })
            else:
                print(f"Manual Search Blocked: {response.status_code}")
    except Exception as e:
        print(f"Manual search error for '{query}': {e}")
    return results

async def search_ddg_instant(query: str, max_results: int = 5):
    """
    DuckDuckGo Instant Answer API backend (api.duckduckgo.com).
    Official JSON API — no key required, works where HTML scraping is blocked.
    Returns instant answer + related topics in the standard result format.
    """
    results = []
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1,
    }
    headers = {
        "User-Agent": "OmniSearch/4.0 (VisionQuantech; +https://apps.visionquantech.com/omni-search/)",
        "Accept": "application/json",
    }
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                # 1. Instant answer abstract as top result
                abstract = (data.get("AbstractText") or "").strip()
                abstract_url = (data.get("AbstractURL") or "").strip()
                abstract_src = (data.get("AbstractSource") or "").strip()
                if abstract and abstract_url:
                    results.append({
                        "title": f"{query} — {abstract_src}" if abstract_src else query,
                        "url": abstract_url,
                        "snippet": abstract[:500],
                        "provider": "ddg_instant",
                    })
                # 2. Related topics as additional results
                for topic in data.get("RelatedTopics", []):
                    if len(results) >= max_results:
                        break
                    # RelatedTopics may contain nested "Topics" groups
                    subtopics = topic.get("Topics") if isinstance(topic, dict) else None
                    items = subtopics if subtopics else [topic]
                    for item in items:
                        if len(results) >= max_results:
                            break
                        if not isinstance(item, dict):
                            continue
                        text = (item.get("Text") or "").strip()
                        first_url = (item.get("FirstURL") or "").strip()
                        if text and first_url:
                            # Title = first sentence-ish, snippet = full text
                            title = text.split(" - ")[0].strip()[:120] or text[:120]
                            results.append({
                                "title": title,
                                "url": first_url,
                                "snippet": text[:500],
                                "provider": "ddg_instant",
                            })
            else:
                print(f"DDG Instant API blocked: {response.status_code}")
    except Exception as e:
        print(f"DDG Instant API error for '{query}': {e}")
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
    Industry-Grade Multi-Provider Search:
    1. Check Cache
    2. Translates query to English (Global Data).
    3. Runs providers in parallel:
       - DDG HTML scraping (search_single) — rich web results
       - DDG Instant Answer API (search_ddg_instant) — official API, resilient
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

    # Parallel multi-provider search tasks
    tasks = []
    for q in queries:
        tasks.append(search_single(q, max_results=max_results))       # Provider 1: DDG HTML
        tasks.append(search_ddg_instant(q, max_results=max_results))   # Provider 2: DDG Instant API
    search_responses = await asyncio.gather(*tasks)

    # Flatten and Deduplicate by URL
    all_results = []
    seen_urls = set()

    for resp in search_responses:
        for item in resp:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                all_results.append(item)

    n_html = sum(1 for r in all_results if r.get("provider") != "ddg_instant")
    n_instant = sum(1 for r in all_results if r.get("provider") == "ddg_instant")
    print(f"Multi-provider search: {n_html} HTML results + {n_instant} Instant API results = {len(all_results)} total.")
    
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
