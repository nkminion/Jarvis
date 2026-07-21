# core/search.py
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from ddgs import DDGS
from config import NUM_SEARCH_RESULTS, MAX_WORKERS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ------------------------------------------
# ⚡ OPTIMIZATIONS APPLIED:
# 1. Caching with LRU (avoids re-searching same query)
# 2. Retry mechanism with exponential backoff
# 3. Threaded fallback for prefetch or parallel search expansion
# 4. Clean text extraction and result deduplication
# ------------------------------------------

@lru_cache(maxsize=64)
def ddg_search(query, top_k=NUM_SEARCH_RESULTS, retries=2, delay=1.5):
    """Perform a DuckDuckGo search with retry + caching."""
    start_time = time.time()
    results = []

    for attempt in range(retries):
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=top_k):
                    title = (r.get("title") or "").strip()
                    link = (r.get("href") or "").strip()
                    snippet = (r.get("body") or "").strip()
                    if title and link:
                        results.append({"title": title, "link": link, "snippet": snippet})
            break  #  Successful, exit retry loop
        except Exception as e:
            logging.warning(f"[Attempt {attempt+1}] DuckDuckGo search failed: {e}")
            time.sleep(delay * (attempt + 1))  # exponential backoff

    # Deduplicate by link
    unique = {r["link"]: r for r in results}.values()
    results = list(unique)[:top_k]

    # Log timing
    elapsed = round(time.time() - start_time, 2)
    logging.info(f"Search for '{query}' → {len(results)} results in {elapsed}s")

    # Fallback
    if not results:
        logging.warning(f"No results found for query: {query}")
        results = ddg_search_lite(query, top_k=top_k)

    return results


def ddg_search_lite(query, top_k=NUM_SEARCH_RESULTS):
    """
    Lightweight fallback that attempts smaller DDG searches
    concurrently for robustness.
    """
    logging.info("Running lightweight fallback search...")
    subqueries = [query, f"{query} summary", f"{query} site:wikipedia.org"]

    results = []
    with ThreadPoolExecutor(max_workers=min(3, MAX_WORKERS)) as executor:
        futures = {executor.submit(_search_single, q, top_k): q for q in subqueries}
        for fut in as_completed(futures):
            try:
                results.extend(fut.result())
            except Exception as e:
                logging.warning(f"Lite search failed for {futures[fut]}: {e}")

    # Deduplicate & truncate
    unique = {r["link"]: r for r in results}.values()
    return list(unique)[:top_k]


def _search_single(query, top_k):
    """Helper for concurrent sub-search."""
    out = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=top_k // 2):
                out.append({
                    "title": (r.get("title") or "").strip(),
                    "link": (r.get("href") or "").strip(),
                    "snippet": (r.get("body") or "").strip(),
                })
    except Exception as e:
        logging.debug(f"Single search error ({query}): {e}")
    return out
