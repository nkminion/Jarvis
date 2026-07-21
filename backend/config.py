# Central configuration for JARVIS

# Summarization model
SUMMARIZER_MODEL = "sshleifer/distilbart-cnn-12-6"

# Maximum tokens for the summary (used in summarizer)
MAX_SUMMARY_TOKENS = 150  # short, concise summary

# SentenceTransformer model for reranking
RERANK_MODEL = "all-MiniLM-L6-v2"

# Number of search results to fetch
NUM_SEARCH_RESULTS = 6

# Maximum pages to fetch for summarization
MAX_PAGES = 3

# Maximum characters per summary (truncate final summary)
MAX_CHARS = 350

# Max workers for concurrent page fetching
MAX_WORKERS = 4

# Optional: rerank pages before summarization
USE_RERANK = True

# Fetch timeout in seconds
TIMEOUT = 10

# Logging level
LOG_LEVEL = "INFO"
