"""Agricultural AI Assistant — "Ask AgriGuard".

Answers free-form farmer questions using the RAG pipeline:

    Farmer Question
         ↓
    Question Processing (language detection + tokenisation)
         ↓
    Knowledge Retrieval (ragService.retrieve)
         ↓
    Relevant Agricultural Information (grounded chunks)
         ↓
    Answer Generation (mock generator OR LLM adapter)
         ↓
    Grounded Answer (with sources + escalation flag)

The answer is ALWAYS grounded in retrieved knowledge. If nothing relevant is
retrieved, the assistant says it cannot answer confidently and recommends an
agronomist — it never invents facts.

Contract: ``answer_agricultural_question(question, opts)`` → AgriculturalAnswer
    ``{answer, language, sources, confidence, needsAgronomist, reason}``

Mirrors ``src/services/aiAssistantService.js``.
"""

import os
import logging

from app.config import settings
from app.services.rag_service import rag_service
from app.services.language_service import language_service
from app.services.escalation_service import escalation_service

logger = logging.getLogger("agriguard.assistant")


def _load_llm_adapter():
    """Lazily load the OpenAI text adapter if we are in real mode with a key."""
    if settings.mode == "openai" and os.getenv("OPENAI_API_KEY"):
        try:
            from app.services.adapters.openai_text_adapter import openai_text_adapter
            return openai_text_adapter
        except Exception:
            # fall back to local generator
            return None
    return None


class AiAssistantService:
    """Ask AgriGuard — RAG-grounded agricultural Q&A."""

    async def answer_agricultural_question(self, question, opts=None):
        """Answer an agricultural question.

        Args:
            question: the farmer's question.
            opts: optional dict with ``language`` (override detected) and
                ``cropId`` (optional crop context).

        Returns:
            ``{answer, language, sources, confidence, needsAgronomist, reason}``.
        """
        opts = opts or {}

        if not question or not question.strip():
            return {
                "answer": (
                    "Tondeka ikibazo cyo kubaza."
                    if opts.get("language") == "rw"
                    else "Please provide a question to ask."
                ),
                "language": opts.get("language") or settings.default_language,
                "sources": [],
                "confidence": 0,
                "needsAgronomist": False,
                "reason": "empty_question",
            }

        lang = opts.get("language") or language_service.detect_language(question) or settings.default_language

        # 1. Retrieve relevant knowledge.
        chunks = rag_service.retrieve(question, {"topK": 3, "cropId": opts.get("cropId")})

        # 2. No retrieval → honest "I don't know" + escalate.
        if not chunks:
            unknown_answer = (
                "Mbabaze ntabwo mbashije kubona amakuru ahuye n'ikibazo cyawe mu bubiko bwacu. "
                "Ngombwa kubaza umuhinzi w'ubuhinzi kugira ngo agufashe."
                if lang == "rw"
                else "I could not find relevant information in our knowledge base for your question. "
                "Please consult an agricultural extension officer for help."
            )
            return {
                "answer": unknown_answer,
                "language": lang,
                "sources": [],
                "confidence": 0.35,
                "needsAgronomist": True,
                "reason": "no_retrieval",
            }

        # 3. Generate a grounded answer.
        llm_adapter = _load_llm_adapter()
        if llm_adapter:
            context = rag_service.build_context(chunks, lang)
            try:
                gen = await llm_adapter.generate(question=question, context=context, language=lang)
                answer = gen["answer"]
                confidence = gen["confidence"]
            except Exception:
                # degrade to local generator if the API fails
                answer, confidence = self._local_generate(question, chunks, lang)
        else:
            answer, confidence = self._local_generate(question, chunks, lang)

        # 4. Escalation: if confidence is low, recommend agronomist.
        escalation = escalation_service.should_escalate(
            {"confidence": confidence, "severity": None, "category": None},
            {},
        )

        # 5. Build sources list for transparency.
        sources = [
            {"title": c["title"], "source": c["source"], "topic": c["topic"]}
            for c in chunks
        ]

        return {
            "answer": answer,
            "language": lang,
            "sources": sources,
            "confidence": confidence,
            "needsAgronomist": escalation["needsAgronomist"],
            "reason": escalation["reason"],
        }

    def _local_generate(self, question, chunks, lang):
        """Local deterministic answer generator (mock mode).

        Composes a coherent grounded answer from the top retrieved chunk. The
        answer explicitly cites the retrieved knowledge.
        """
        top = chunks[0]
        is_rw = lang == "rw"
        content = top["contentRw"] if is_rw else top["contentEn"]
        if not content:
            content = top["contentEn"]

        if is_rw:
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

        # Confidence scales with retrieval score — capped to keep it honest.
        confidence = min(0.5 + top["score"] * 0.08, 0.85)

        return answer, confidence


# Module-level singleton.
ai_assistant_service = AiAssistantService()
