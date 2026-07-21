import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from .search import ddg_search
from .fetcher import fetch_page_text
from .rerank import rerank_snippets
from .summarize import summarize
from config import MAX_PAGES, MAX_CHARS, MAX_WORKERS, NUM_SEARCH_RESULTS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ------------------------------
# ⚡ Optimizations:
# - Cached search & summaries
# - Concurrent fetch with ThreadPool
# - Truncate long texts for faster summarization
# - Returns single short summary + multiple sources
# ------------------------------

@lru_cache(maxsize=32)
def cached_search(query):
    return ddg_search(query, top_k=NUM_SEARCH_RESULTS)

def _fetch_pages(results, max_pages=MAX_PAGES, timeout=10, max_workers=MAX_WORKERS):
    pages = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_meta = {executor.submit(fetch_page_text, r["link"]): r for r in results[:max_pages]}
        for fut in as_completed(future_to_meta):
            meta = future_to_meta[fut]
            try:
                text = fut.result(timeout=timeout)
                pages.append({
                    "title": meta.get("title", ""),
                    "link": meta.get("link", ""),
                    "text": text
                })
            except Exception as e:
                logging.warning("⚠️ Error fetching page: %s", e)
    return pages

@lru_cache(maxsize=64)
def cached_summary(text):
    try:
        return summarize(text).strip()
    except Exception as e:
        logging.warning(f"Summarization failed: {e}")
        return ""

def handler(query, top_k=3):
    """
    Returns:
    {
      "answer": "Single concise summary",
      "sources": [{"title":..., "link":...}],
      "meta": {...}
    }
    """
    if not query or len(query.strip()) == 0:
        return {"answer": "Please enter a valid query.", "sources": [], "meta": {}}

    # 1️ Cached Search
    results = cached_search(query)
    if not results:
        return {"answer": "No search results found.", "sources": [], "meta": {}}

    # 2️ Prepare snippets for reranking
    snippets = [
        {
            "text": (r.get("snippet", "") + " " + r.get("title", "")),
            "link": r["link"],
            "title": r.get("title", "")
        }
        for r in results
    ]

    # 3️ Rerank snippets
    ranked = rerank_snippets(query, snippets, top_k=top_k)

    # 4️ Fetch full page text
    pages = _fetch_pages(ranked, max_pages=top_k)

    if not pages:
        return {"answer": "No content could be fetched.", "sources": [], "meta": {"results_count": len(results)}}

    # 5️ Combine all page texts for a single summary
    combined_text = " ".join((p.get("text") or "")[:3000] for p in pages)

    if not combined_text.strip():
        return {"answer": "No text content available to summarize.", "sources": [{"title": p["title"], "link": p["link"]} for p in pages], "meta": {"results_count": len(results)}}

    final_summary = cached_summary(combined_text)

    # Truncate summary if too long
    if len(final_summary) > MAX_CHARS:
        final_summary = final_summary[:MAX_CHARS].rsplit('.', 1)[0] + "..."

    return {
        "answer": final_summary or "No concise summary could be generated.",
        "sources": [{"title": p["title"], "link": p["link"]} for p in pages],
        "meta": {"results_count": len(results)}
    }
