# core/fetcher.py
import logging
import hashlib
import time
import os
import httpx
from functools import lru_cache
from selectolax.parser import HTMLParser
from newspaper import Article

# Configurable constants
CACHE_DIR = "cache_pages"
TIMEOUT = 10
MAX_RETRIES = 2
MAX_LENGTH = 5000

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(url):
    """Generate local cache filename for a given URL."""
    return os.path.join(CACHE_DIR, hashlib.md5(url.encode()).hexdigest() + ".txt")


@lru_cache(maxsize=256)
def fetch_page_text(url: str, timeout: int = TIMEOUT) -> str:
    """
    Fetch and clean webpage text with caching and fallbacks.
    Optimized for speed and reliability.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; JARVIS/1.0)"}
    cache_file = _cache_path(url)

    # Step 1: Serve from cache if exists
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = f.read()
            if cached:
                logging.debug(f"Cache hit for {url}")
                return cached
        except Exception:
            pass

    # Step 2: Fast asynchronous request (httpx)
    html = ""
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
                r = client.get(url)
                r.raise_for_status()
                html = r.text
                break
        except Exception as e:
            logging.warning(f"[Attempt {attempt+1}] Failed to fetch {url}: {e}")
            time.sleep(0.8)
    else:
        return ""

    # Step 3: Try Newspaper3k extraction (best quality)
    try:
        a = Article(url)
        a.download(input_html=html)
        a.parse()
        if len(a.text) > 120:
            _save_to_cache(cache_file, a.text)
            return a.text
    except Exception:
        pass

    # Step 4: Fast fallback with Selectolax (much faster than BeautifulSoup)
    try:
        parser = HTMLParser(html)
        texts = []
        for node in parser.css("p"):
            t = node.text(strip=True)
            if len(t) > 40:
                texts.append(t)
        text = "\n".join(texts)
        text = text[:MAX_LENGTH]
        _save_to_cache(cache_file, text)
        return text
    except Exception as e:
        logging.error(f"HTML parsing failed for {url}: {e}")
        return ""


def _save_to_cache(path, text):
    """Save fetched text to local cache."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        logging.warning(f"Failed to write cache {path}: {e}")
