"""Retrieval-Augmented Generation (RAG) for agriculture (sections 13/14).

Architecture:
    Farmer Question -> embedding -> knowledge retrieval -> relevant info -> answer

Two interchangeable retrievers implement the same ``retrieve`` contract:

1. ``EmbeddingsRetriever`` — REAL semantic retrieval:
   - sentence-transformers model (``all-MiniLM-L6-v2``) embeds the query and the
     knowledge articles.
   - FAISS (``faiss-cpu``) indexes the article embeddings for fast similarity
     search (cosine similarity via L2-normalised vectors + inner-product index).
2. ``KeywordRetriever`` — deterministic keyword-overlap fallback (no heavy deps).

``get_retriever()`` returns the embeddings retriever if its deps are installed
and the index is built; otherwise the keyword retriever. The notebook builds the
embeddings index; ``retrieve_agricultural_knowledge`` works with whichever is
active.

Honest limitation (section 27): the embeddings model is a general-purpose
English mini-model; Kinyarwanda retrieval quality must be validated.
"""

import re
from typing import Dict, List, Optional

from ai.src import knowledge

# Optional heavy dependencies.
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    import faiss
    EMBEDDINGS_AVAILABLE = True
except Exception:  # pragma: no cover
    EMBEDDINGS_AVAILABLE = False


# ── Keyword retriever (fallback) ───────────────────────────────────────────────
_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "of", "in", "on", "at",
    "to", "for", "with", "from", "and", "or", "but", "not", "i", "you", "my",
    "how", "what", "do", "should", "can", "by", "ya", "na", "ku", "mu",
}
_NON_TOKEN = re.compile(r"[^\w\s]", re.UNICODE)


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    text = _NON_TOKEN.sub(" ", text.lower()).replace("_", " ")
    return [t for t in text.split() if len(t) > 2 and t not in _STOPWORDS]


def _score_keyword(article: Dict, query_tokens: List[str]) -> float:
    if not query_tokens:
        return 0.0
    score = 0.0
    for kw in article.get("keywords", []):
        kw_l = kw.lower()
        if any(kw_l in q or q in kw_l for q in query_tokens):
            score += 3
    title_tokens = set(_tokenize(article.get("title", "")))
    for q in query_tokens:
        if q in title_tokens:
            score += 2
    content_tokens = set(_tokenize(article.get("content_en", "") + " " + article.get("content_rw", "")))
    for q in query_tokens:
        if q in content_tokens:
            score += 1
    return score


class KeywordRetriever:
    """Deterministic keyword-overlap retriever — always available."""

    name = "keyword"

    def retrieve(self, query: str, top_k: int = 3, crop_id: Optional[str] = None) -> List[Dict]:
        articles = knowledge.knowledge_articles_as_dicts()
        query_tokens = _tokenize(query)

        if crop_id and crop_id != "unknown":
            articles = [
                a for a in articles
                if a["crop"] == crop_id
                or (a["crop"] and crop_id in a["crop"].split(","))
                or a["topic"] in ("crop-overview", "prevention")
            ]

        scored = [(a, _score_keyword(a, query_tokens)) for a in articles]
        scored = [s for s in scored if s[1] > 0]
        scored.sort(key=lambda x: x[1], reverse=True)
        scored = scored[:top_k]

        return [
            {
                "id": a["id"], "title": a["title"], "content": a["content_en"],
                "content_en": a["content_en"], "content_rw": a["content_rw"],
                "crop": a["crop"], "topic": a["topic"], "score": float(score),
                "source": a["source"],
            }
            for a, score in scored
        ]


# ── Embeddings retriever (sentence-transformers + FAISS) ──────────────────────
class EmbeddingsRetriever:
    """Semantic retriever using sentence-transformers + FAISS (REAL ML)."""

    name = "embeddings"
    MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(self):
        if not EMBEDDINGS_AVAILABLE:
            raise RuntimeError("sentence-transformers + faiss-cpu not installed")
        self.model = None
        self.index = None
        self.articles: List[Dict] = []
        self.built = False

    def _ensure_model(self):
        if self.model is None:
            self.model = SentenceTransformer(self.MODEL_NAME)

    def build_index(self) -> int:
        """Embed all knowledge articles and build the FAISS index. Returns count."""
        self._ensure_model()
        self.articles = knowledge.knowledge_articles_as_dicts()
        texts = [f"{a['title']}. {a['content_en']} {a['content_rw']}" for a in self.articles]
        emb = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        emb = np.ascontiguousarray(emb, dtype="float32")
        self.index = faiss.IndexFlatIP(emb.shape[1])
        self.index.add(emb)
        self.built = True
        return len(self.articles)

    def retrieve(self, query: str, top_k: int = 3, crop_id: Optional[str] = None) -> List[Dict]:
        if not self.built:
            self.build_index()
        self._ensure_model()
        q_emb = self.model.encode([query], normalize_embeddings=True, show_progress_bar=False)
        q_emb = np.ascontiguousarray(q_emb, dtype="float32")

        # Fetch a larger candidate pool, then optionally filter by crop, then
        # return the top_k after filtering.
        k = min(max(top_k * 3, top_k), len(self.articles))
        scores, indices = self.index.search(q_emb, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            a = self.articles[int(idx)]
            if crop_id and crop_id != "unknown":
                if not (
                    a["crop"] == crop_id
                    or (a["crop"] and crop_id in a["crop"].split(","))
                    or a["topic"] in ("crop-overview", "prevention")
                ):
                    continue
            results.append(
                {
                    "id": a["id"], "title": a["title"], "content": a["content_en"],
                    "content_en": a["content_en"], "content_rw": a["content_rw"],
                    "crop": a["crop"], "topic": a["topic"], "score": float(score),
                    "source": a["source"],
                }
            )
            if len(results) >= top_k:
                break
        return results


# ── Module-level singleton + public API ──────────────────────────────────────
_EMBEDDINGS_RETRIEVER: Optional[EmbeddingsRetriever] = None


def is_embeddings_available() -> bool:
    return EMBEDDINGS_AVAILABLE and _EMBEDDINGS_RETRIEVER is not None and _EMBEDDINGS_RETRIEVER.built


def get_retriever():
    """Return the embeddings retriever if available/built, else the keyword one."""
    if is_embeddings_available():
        return _EMBEDDINGS_RETRIEVER
    return KeywordRetriever()


def build_embeddings_index(model_name: str = None) -> int:
    """Build (or rebuild) the FAISS embeddings index. Returns the article count."""
    global _EMBEDDINGS_RETRIEVER
    if not EMBEDDINGS_AVAILABLE:
        raise RuntimeError("sentence-transformers + faiss-cpu not installed")
    _EMBEDDINGS_RETRIEVER = EmbeddingsRetriever()
    if model_name:
        _EMBEDDINGS_RETRIEVER.MODEL_NAME = model_name
    return _EMBEDDINGS_RETRIEVER.build_index()


def retrieve_agricultural_knowledge(
    query: str,
    top_k: int = 3,
    crop_id: Optional[str] = None,
    use_embeddings: bool = True,
) -> List[Dict]:
    """Retrieve the most relevant knowledge articles for a farmer question.

    Returns a list of chunks (best-first). Each chunk records which backend
    produced it via the retriever's ``name`` (see ``get_retriever``).
    """
    retriever = get_retriever() if use_embeddings else KeywordRetriever()
    return retriever.retrieve(query, top_k=top_k, crop_id=crop_id)


def retriever_method() -> str:
    """Return 'embeddings' or 'keyword' — which backend is currently active."""
    return get_retriever().name


def build_context(chunks: List[Dict], lang: str = "en") -> str:
    """Compose retrieved chunks into a single grounded context string."""
    if not chunks:
        return ""
    parts = []
    for i, c in enumerate(chunks):
        content = c["content_rw"] if lang == "rw" else c["content_en"]
        if not content:
            content = c["content_en"]
        parts.append(f"[{i + 1}] {c['title']}\n{content}\n(source: {c['source']})")
    return "\n\n".join(parts)
