"""RAG (Retrieval-Augmented Generation) Service.

Prototype retrieval layer. Does NOT use a vector database — it uses a
transparent keyword-overlap scorer over the in-memory knowledge base.

The interface is intentionally identical to a real embeddings-based retriever
so this module can be swapped for:
    - sentence-transformers embeddings + cosine similarity
    - pgvector / Pinecone / Chroma
    - OpenAI embeddings API

Contract: ``retrieve(query, topK=3, cropId=None)`` → list of chunks with
``{id, title, content, contentEn, contentRw, crop, topic, score, source}``.

The returned chunks are passed to the assistant service to ground answers in
retrieved agricultural information rather than allowing the model to invent
facts.

HONESTY NOTE: this is a keyword-scoring prototype, NOT a semantic search engine.
Mirrors ``src/services/ragService.js``.
"""

import re

from app.data import knowledge_base as kb

# Stopwords (English + short low-signal Kinyarwanda particles). Identical to
# the JavaScript STOPWORDS set.
STOPWORDS = {
    # English stopwords
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "what", "who", "whom", "whose", "which", "that", "this", "these", "those",
    "of", "in", "on", "at", "to", "for", "with", "by", "from", "as", "into",
    "and", "or", "but", "not", "no", "nor", "so", "yet", "if", "then",
    "do", "does", "did", "doing", "have", "has", "had", "having",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their",
    "how", "why", "when", "where", "can", "could", "should", "would", "will",
    # common Kinyarwanda particles (short, low-signal)
    "bya", "ya", "na", "ku", "mu", "bw", "cy", "by",
}

# Approximates the JS ``/[^\p{L}\p{N}\s]/gu`` replacement. ``\w`` with the
# UNICODE flag matches letters, digits and underscore; we strip the underscore
# afterwards so only letters/numbers/space remain.
_NON_TOKEN = re.compile(r"[^\w\s]", re.UNICODE)


def tokenize(text):
    """Lowercase, strip punctuation, split on whitespace, drop stopwords and short tokens."""
    if not text:
        return []
    text = text.lower()
    text = _NON_TOKEN.sub(" ", text).replace("_", " ")
    return [t for t in text.split() if len(t) > 2 and t not in STOPWORDS]


def _score_article(article, query_tokens):
    """Transparent keyword-overlap score for one knowledge article."""
    if not query_tokens:
        return 0
    score = 0

    # Keyword-field match (high weight).
    for kw in article.get("keywords", []):
        kw_lower = kw.lower()
        if any(kw_lower in q or q in kw_lower for q in query_tokens):
            score += 3

    # Title match (medium weight).
    title_tokens = tokenize(article.get("title", ""))
    for q in query_tokens:
        if q in title_tokens:
            score += 2

    # Content match (low weight).
    content_tokens = tokenize((article.get("contentEn", "") or "") + " " + (article.get("contentRw", "") or ""))
    for q in query_tokens:
        if q in content_tokens:
            score += 1

    return score


class RagService:
    """Keyword-overlap retrieval over the prototype knowledge base."""

    def retrieve(self, query, opts=None):
        """Retrieve the most relevant knowledge articles for a query.

        Args:
            query: the farmer's question.
            opts: optional dict with ``topK`` (default 3) and ``cropId``.

        Returns:
            list of ``{id, title, content, contentEn, contentRw, crop, topic,
            score, source}``, ranked by score descending.
        """
        opts = opts or {}
        top_k = opts.get("topK") or 3
        articles = kb.get_knowledge_articles()
        query_tokens = tokenize(query)

        filtered = articles
        if opts.get("cropId") and opts["cropId"] != "unknown":
            crop_id = opts["cropId"]
            # Keep crop-specific articles + problem articles that affect this
            # crop, plus general crop-overview/prevention articles.
            filtered = [
                a
                for a in articles
                if a.get("crop") == crop_id
                or (a.get("crop") and crop_id in a["crop"].split(","))
                or a.get("topic") in ("crop-overview", "prevention")
            ]

        scored = [
            (a, _score_article(a, query_tokens))
            for a in filtered
        ]
        scored = [x for x in scored if x[1] > 0]
        scored.sort(key=lambda x: x[1], reverse=True)
        scored = scored[:top_k]

        return [
            {
                "id": a["id"],
                "title": a["title"],
                "content": a["contentEn"],
                "contentEn": a["contentEn"],
                "contentRw": a["contentRw"],
                "crop": a["crop"],
                "topic": a["topic"],
                "score": score,
                "source": a["source"],
            }
            for a, score in scored
        ]

    def build_context(self, chunks, lang="en"):
        """Build a grounded context string from retrieved chunks (for prompt injection)."""
        if not chunks:
            return ""
        parts = []
        for i, c in enumerate(chunks):
            content = c["contentRw"] if lang == "rw" else c["contentEn"]
            if not content:
                content = c["contentEn"]
            parts.append(f"[{i + 1}] {c['title']}\n{content}\n(source: {c['source']})")
        return "\n\n".join(parts)


# Module-level singleton.
rag_service = RagService()
