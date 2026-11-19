"""Agricultural AI assistant — "Ask AgriGuard" (section 15).

Answers a free-form farmer question by retrieving relevant knowledge (RAG) and
composing a grounded answer. The answer is ALWAYS grounded in retrieved
knowledge; if nothing relevant is retrieved, the assistant says so honestly and
recommends an agronomist — it never invents facts.

``answer_farmer_question(question, language="auto")``:
    1. Detect/accept language (en/rw).
    2. Retrieve relevant agricultural knowledge (embeddings or keyword fallback).
    3. Compose a grounded answer from the top retrieved chunk.
    4. Return the response in the appropriate language.
    5. Flag when expert help is recommended.

Honest limitation (section 27): Kinyarwanda generation here is template-based
retrieval grounding, not a generative LLM. The notebook shows how an LLM adapter
(OpenAI/Hugging Face) could be plugged in for real generation, with the API key
kept in an environment variable (section 31).
"""

import os
from typing import Optional

from ai.src import rag
from ai.src.multilingual import resolve_language, get_message
from ai.src.alert_logic import needs_agronomist
from ai.src.models import AssistantAnswer


def _load_llm_adapter():
    """Optionally load a real LLM adapter if an API key is configured.

    Kept minimal: if OPENAI_API_KEY is set we could call the OpenAI Chat API to
    GENERATE (not just retrieve) the answer. For the prototype we compose a
    grounded answer locally from the retrieved chunk, which is fully offline and
    needs no key — so this returns None by default.
    """
    return None  # generation stays local + grounded; swap in an LLM here later.


def _local_answer(question, chunks, lang):
    """Compose a grounded answer from the top retrieved chunk (offline)."""
    top = chunks[0]
    content = top["content_rw"] if lang == "rw" else top["content_en"]
    if not content:
        content = top["content_en"]

    if lang == "rw":
        answer = (
            f"Ubu buzima bw'ubuhinzi: {content}\n\n"
            f"Iyi nama ivuye ku bubiko bwacu bw'ubuhinzi (source: {top['source']}). "
            f"Niba ikibazo gikomeye, asaba inama z'umuhinzi w'ubuhinzi."
        )
    else:
        answer = (
            f"Based on our agricultural knowledge base: {content}\n\n"
            f"This information comes from: {top['source']}. "
            f"If the problem is serious, please consult an agricultural extension officer."
        )
    # Confidence scales with retrieval score, capped to stay honest.
    confidence = min(0.5 + top["score"] * 0.08, 0.85)
    return answer, confidence


def answer_farmer_question(question: str, language: str = "auto", crop_id: Optional[str] = None,
                            use_embeddings: bool = True) -> AssistantAnswer:
    """Answer a farmer's agricultural question.

    Args:
        question: the farmer's question.
        language: "auto" (detect) or explicit "en"/"rw".
        crop_id: optional crop context to focus retrieval.
        use_embeddings: use semantic retrieval if available (else keyword).

    Returns:
        AssistantAnswer dataclass (call ``.to_dict()`` for JSON).
    """
    if not question or not question.strip():
        return AssistantAnswer(
            question=question or "",
            answer=(
                "Tondeka ikibazo cyo kubaza."
                if language == "rw"
                else "Please provide a question to ask."
            ),
            language=language if language in ("en", "rw") else "en",
            reason="empty_question",
        )

    lang = resolve_language(explicit=None if language == "auto" else language, text=question)

    chunks = rag.retrieve_agricultural_knowledge(question, top_k=3, crop_id=crop_id, use_embeddings=use_embeddings)
    method = rag.retriever_method()

    if not chunks:
        unknown = (
            "Mbabaze ntabwo mbashije kubona amakuru ahuye n'ikibazo cyawe mu bubiko bwacu. "
            "Ngombwa kubaza umuhinzi w'ubuhinzi kugira ngo agufashe."
            if lang == "rw"
            else "I could not find relevant information in our knowledge base for your question. "
                 "Please consult an agricultural extension officer for help."
        )
        return AssistantAnswer(
            question=question, answer=unknown, language=lang,
            confidence=0.35, needs_agronomist=True, reason="no_retrieval",
            retrieval_method=method,
        )

    llm = _load_llm_adapter()
    if llm:
        try:
            context = rag.build_context(chunks, lang)
            gen = llm.generate(question=question, context=context, language=lang)
            answer, confidence = gen["answer"], gen["confidence"]
        except Exception:
            answer, confidence = _local_answer(question, chunks, lang)
    else:
        answer, confidence = _local_answer(question, chunks, lang)

    escalation = needs_agronomist(confidence, None, None)

    sources = [{"title": c["title"], "source": c["source"], "topic": c["topic"]} for c in chunks]

    return AssistantAnswer(
        question=question,
        answer=answer,
        language=lang,
        sources=sources,
        confidence=round(confidence, 2),
        needs_agronomist=escalation.needs_agronomist,
        reason=escalation.reason,
        retrieval_method=method,
    )
