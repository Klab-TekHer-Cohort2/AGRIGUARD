"""OpenAI Text Adapter — LLM completion for the AI assistant (REAL mode).

Used by aiAssistantService when AI_MODE=openai and OPENAI_API_KEY is set.
Generates a grounded answer from retrieved RAG context.

Mirrors ``src/services/adapters/openaiTextAdapter.js`` (axios → httpx).
"""

import os

import httpx

OPENAI_URL = os.getenv("OPENAI_URL", "https://api.openai.com/v1/chat/completions")
OPENAI_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")


def _build_system_prompt(lang):
    lang_name = "Kinyarwanda" if lang == "rw" else "English"
    return (
        "You are AgriGuard, an agricultural assistant for Rwandan smallholder farmers.\n"
        "Answer the farmer's question using ONLY the provided agricultural context.\n"
        "If the context does not contain the answer, say you cannot answer confidently and "
        "recommend consulting an agronomist.\n"
        f"Respond in {lang_name}.\n"
        "Keep the answer practical, short, and grounded in the context.\n"
        "Do not invent facts or recommend specific pesticides. Where treatment depends on "
        "local guidance, direct the farmer to agricultural professionals."
    )


class OpenAITextAdapter:
    """Real LLM completion adapter calling the OpenAI Chat Completions API."""

    async def generate(self, question=None, context=None, language=None):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        body = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": _build_system_prompt(language)},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
            "max_tokens": 400,
            "temperature": 0.3,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                OPENAI_URL,
                json=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        answer = (data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
        return {"answer": answer, "confidence": 0.8}


# Module-level singleton.
openai_text_adapter = OpenAITextAdapter()
