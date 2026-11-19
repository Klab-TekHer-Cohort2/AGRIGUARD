"""Voice Assistant orchestrator — the complete voice pipeline for AgriGuard.

Connects STT → Agricultural AI → TTS in one callable function.

Full pipeline:
    Audio file
        ↓  speech_to_text()          (stt.py — Whisper or Stub)
    Transcribed text + language
        ↓  answer_farmer_question()   (assistant.py — RAG-grounded)
    AI answer text
        ↓  text_to_speech()           (tts.py — gTTS, pyttsx3, or Stub)
    Audio response file
        ↓
    Return structured result dict

Voice is NOT a separate AI — it is another input/output channel to the same
agricultural AI layer already used by the smartphone and USSD flows. The same
RAG, escalation, and multilingual logic applies.

Two public functions:
    voice_farmer_assistant(audio_path, language) — voice Q&A
    voice_crop_report(audio_path, crop, image, location, language) — voice + image
"""

import os
from typing import Any, Dict, Optional

from ai.src.stt import speech_to_text
from ai.src.tts import text_to_speech
from ai.src.assistant import answer_farmer_question
from ai.src.crop_analysis import analyze_report, ussd_format
from ai.src.multilingual import resolve_language, get_message


def _voice_escalation_text(lang: str) -> str:
    """Standard spoken escalation message (section 8 requirement)."""
    if lang == "rw":
        return (
            "Ikibazo cyawe ntikibashije kumenya neza. "
            "Raporo yawe yoherejwe ku muhinzi w'ubuhinzi kugira ngo agufashe."
        )
    return (
        "Your problem could not be identified confidently. "
        "Your report will be sent to an agronomist for further assistance."
    )


def voice_farmer_assistant(
    audio_path: str,
    language: str = "auto",
    tts_output_path: str = "voice_response.mp3",
    use_real_stt: bool = True,
    tts_prefer: str = "gtts",
) -> Dict[str, Any]:
    """Complete voice pipeline: audio in → spoken agricultural answer out.

    Args:
        audio_path:      path to the farmer's audio file (WAV/MP3/M4A/FLAC).
                         In Colab, use the uploaded file path.
        language:        "en", "rw", or "auto" (auto-detect from speech).
        tts_output_path: where to save the spoken AI response.
        use_real_stt:    True = use Whisper if available; False = use Stub.
        tts_prefer:      "gtts" (default) or "pyttsx3".

    Returns:
        dict with:
            transcribed_text   — what the STT heard
            language           — detected/confirmed language ("en" or "rw")
            answer_text        — AI-generated agricultural answer
            audio_path         — path to the spoken response audio file
            confidence         — AI answer confidence (0–1)
            needs_agronomist   — True if escalation is required
            escalation_reason  — why escalation was triggered (or "none")
            stt_source         — "real-whisper" or "stub-simulated"
            tts_source         — "real-gtts" / "real-pyttsx3" / "stub-simulated"
            rw_tts_note        — Kinyarwanda TTS limitation note (or None)
            sources            — RAG knowledge sources used
    """
    # ── Step 1: Speech-to-Text ────────────────────────────────────────────────
    stt_result = speech_to_text(
        audio_path=audio_path,
        language=language,
        use_real=use_real_stt,
    )
    transcribed_text = stt_result["text"]
    detected_lang = stt_result["language"]

    # Resolve final language: explicit override wins, else STT detection.
    final_lang = resolve_language(
        explicit=None if language == "auto" else language,
        text=transcribed_text,
    )
    # Trust STT-detected language if it is a supported code.
    if detected_lang in ("en", "rw") and language == "auto":
        final_lang = detected_lang

    # ── Step 2: Agricultural AI (same pipeline as text channel) ──────────────
    ai_result = answer_farmer_question(
        question=transcribed_text,
        language=final_lang,
        use_embeddings=True,
    )

    answer_text = ai_result.answer
    needs_agro = ai_result.needs_agronomist

    # ── Step 3: Responsible-AI — spoken escalation message ───────────────────
    if needs_agro:
        # Prepend a clear spoken escalation notice before the full answer.
        escalation_prefix = _voice_escalation_text(final_lang)
        answer_text = f"{escalation_prefix} {answer_text}"

    # ── Step 4: Text-to-Speech ────────────────────────────────────────────────
    tts_result = text_to_speech(
        text=answer_text,
        language=final_lang,
        output_path=tts_output_path,
        prefer=tts_prefer,
    )

    return {
        "transcribed_text": transcribed_text,
        "language": final_lang,
        "answer_text": answer_text,
        "audio_path": tts_result["audio_path"],
        "confidence": ai_result.confidence,
        "needs_agronomist": needs_agro,
        "escalation_reason": ai_result.reason,
        "stt_source": stt_result["source"],
        "tts_source": tts_result["source"],
        "rw_tts_note": tts_result.get("rw_tts_note"),
        "sources": ai_result.sources,
        "stt_note": stt_result.get("note"),
    }


def voice_crop_report(
    audio_path: str,
    crop: str,
    image: Optional[Any] = None,
    location: Optional[Dict] = None,
    language: str = "auto",
    tts_output_path: str = "crop_report_response.mp3",
    use_real_stt: bool = True,
    tts_prefer: str = "gtts",
    vision_mode: str = "simulated",
) -> Dict[str, Any]:
    """Voice + image combined crop report pipeline (section 5 requirement).

    A farmer provides:
        - a photo of the crop plant (image)
        - a voice description (audio_path)
        - crop name + location

    The pipeline:
        1. STT   → transcribe voice description
        2. Vision → analyse image (simulated or real CNN)
        3. AI    → classify problem, severity, confidence, recommendation
        4. TTS   → speak the recommendation back to the farmer

    Args:
        audio_path:   farmer's voice description audio file.
        crop:         crop name ("Maize", "Beans", etc.).
        image:        image filename/bytes/URL passed to vision backend.
        location:     optional {"lat", "lng", "community"}.
        language:     "en", "rw", or "auto".
        tts_output_path: where to save the spoken response.
        use_real_stt: True = Whisper if available; False = Stub.
        tts_prefer:   "gtts" or "pyttsx3".
        vision_mode:  "simulated" (default) or "real" (needs CNN weights).

    Returns:
        dict with: transcribed_text, language, crop_analysis (CropAnalysisResult
        dict), answer_text, audio_path, needs_agronomist, stt_source, tts_source.
    """
    # ── Step 1: STT ───────────────────────────────────────────────────────────
    stt_result = speech_to_text(
        audio_path=audio_path,
        language=language,
        use_real=use_real_stt,
    )
    transcribed_text = stt_result["text"]
    detected_lang = stt_result["language"]

    final_lang = resolve_language(
        explicit=None if language == "auto" else language,
        text=transcribed_text,
    )
    if detected_lang in ("en", "rw") and language == "auto":
        final_lang = detected_lang

    # ── Step 2 + 3: Vision + Agricultural AI ─────────────────────────────────
    # analyze_report() is a regular synchronous function — call it directly.
    result = analyze_report(
        crop=crop,
        description=transcribed_text,
        image=image,
        location=location,
        language=final_lang,
        vision_mode=vision_mode,
    )

    # Build the spoken response from the structured analysis.
    recs = result.recommendation or []
    if final_lang == "rw":
        answer_text = (
            f"{get_message('possible_problem', 'rw')}: "
            f"{result.possible_problem or get_message('unknown_problem', 'rw')}. "
            f"{get_message('severity', 'rw')}: {result.severity}. "
            f"{get_message('advice', 'rw')}: {recs[0] if recs else ''}"
        )
    else:
        answer_text = (
            f"{get_message('possible_problem', 'en')}: "
            f"{result.possible_problem or get_message('unknown_problem', 'en')}. "
            f"{get_message('severity', 'en')}: {result.severity}. "
            f"{get_message('advice', 'en')}: {recs[0] if recs else ''}"
        )

    if result.needs_agronomist:
        escalation_prefix = _voice_escalation_text(final_lang)
        answer_text = f"{escalation_prefix} {answer_text}"

    # ── Step 4: TTS ───────────────────────────────────────────────────────────
    tts_result = text_to_speech(
        text=answer_text,
        language=final_lang,
        output_path=tts_output_path,
        prefer=tts_prefer,
    )

    return {
        "transcribed_text": transcribed_text,
        "language": final_lang,
        "crop_analysis": result.to_dict(),
        "answer_text": answer_text,
        "audio_path": tts_result["audio_path"],
        "needs_agronomist": result.needs_agronomist,
        "escalation_reason": result.escalation_reason,
        "stt_source": stt_result["source"],
        "tts_source": tts_result["source"],
        "rw_tts_note": tts_result.get("rw_tts_note"),
        "vision_source": result.vision_source,
        "stt_note": stt_result.get("note"),
    }
