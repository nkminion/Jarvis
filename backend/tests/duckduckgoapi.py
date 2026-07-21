from duckduckgo_search import DDGS
search_query = "Who is Devi from Never Have I ever"

results = DDGS().text(
    keywords=search_query,
    max_results=5
)

print(results)