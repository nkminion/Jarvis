from sentence_transformers import SentenceTransformer, util
import torch
from config import RERANK_MODEL

_model = None

def _get_model():
    """Load the rerank model once."""
    global _model
    if _model is None:
        _model = SentenceTransformer(RERANK_MODEL)
    return _model

def rerank_snippets(query, snippets, top_k=3):
    """
    Rerank search snippets or pages by semantic similarity to query.
    Keeps top_k most relevant items.
    
    Args:
        query (str): User query
        snippets (list of dict): Each dict has 'text', 'link', 'title'
        top_k (int): Number of top results to keep
    
    Returns:
        list of dict: top_k ranked snippets
    """
    if not snippets:
        return []

    model = _get_model()
    # Encode query and snippets
    q_emb = model.encode(query, convert_to_tensor=True)
    emb = model.encode([s["text"] for s in snippets], convert_to_tensor=True)

    # Compute cosine similarity scores
    scores = util.cos_sim(q_emb, emb)[0]

    # Get top_k indices
    idxs = torch.argsort(scores, descending=True).tolist()
    top_snippets = [snippets[i] for i in idxs[:top_k]]

    return top_snippets
