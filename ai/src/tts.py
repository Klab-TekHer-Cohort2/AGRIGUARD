"""Text-to-Speech (TTS) for AgriGuard voice output.

Converts the AI-generated agricultural answer into spoken audio so the farmer
can hear the response — essential for IVR (Interactive Voice Response) channels
and low-literacy users.

THREE BACKENDS — clearly distinguished:

1. ``GttsTTS`` — REAL TTS using Google Text-to-Speech (gTTS, free, offline-capable
   after first use). Supports many languages including English.
   KINYARWANDA LIMITATION: gTTS does NOT have a dedicated Kinyarwanda voice.
   For Kinyarwanda text, the system uses English TTS as a fallback, which
   produces an English-accented pronunciation of Kinyarwanda words — NOT
   native Kinyarwanda speech. This limitation is always documented in the
   output (``rw_tts_note``).

2. ``Pyttsx3TTS`` — offline TTS using the pyttsx3 library (uses the OS's
   built-in speech synthesiser). Works fully offline, no network needed.
   KINYARWANDA LIMITATION: pyttsx3 uses whatever voices your OS has installed.
   Most systems only have English voices; there is no Kinyarwanda voice.
   Falls back to the first available English-like voice.

3. ``StubTTS`` — deterministic fallback when neither gTTS nor pyttsx3 is
   installed. Creates a minimal silent WAV file so the pipeline always
   produces an audio path without crashing. Output is tagged
   ``source = "stub-simulated"`` — no actual speech is generated.

KINYARWANDA TTS REALITY (honest documentation):
   Native-quality Kinyarwanda TTS is not freely available in a pip-installable
   package as of 2024. Options being developed:
   - Mozilla TTS (https://github.com/mozilla/TTS) — Kinyarwanda voice being
     researched but not production-ready.
   - Google Cloud TTS / AWS Polly — no Kinyarwanda voice available.
   - Practical workaround for demos: generate English audio, label it clearly.
   - For production: commission a Kinyarwanda voice actor for pre-recorded
     response phrases, or partner with RISA / local speech-tech researchers.

INSTALL (Colab):
   pip install gTTS pyttsx3
   # gTTS requires internet for the first synthesis; subsequent may be cached.
   # pyttsx3 is fully offline.

API KEY: None required for gTTS or pyttsx3.
"""

import os
import struct
import wave
from typing import Dict, Optional

# ── Detect optional TTS libraries ────────────────────────────────────────────
try:
    from gtts import gTTS as _gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import pyttsx3 as _pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


# Language codes for gTTS (it uses IETF BCP 47 tags, not ISO 639-1).
_GTTS_LANG_MAP = {
    "en": "en",
    "rw": "en",   # No Kinyarwanda voice — fall back to English TTS
}

_RW_TTS_NOTE = (
    "LIMITATION: No Kinyarwanda TTS voice is available. "
    "The audio was generated using an English voice reading Kinyarwanda text, "
    "which will NOT sound like native Kinyarwanda speech. "
    "For production use, record native Kinyarwanda speaker audio."
)


def _ensure_dir(path: str) -> str:
    """Create parent directories for path if they don't exist."""
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    return path


# ── gTTS backend ──────────────────────────────────────────────────────────────
class GttsTTS:
    """Real TTS using Google Text-to-Speech (gTTS). Requires internet."""

    name = "gtts"
    source = "real-gtts"

    def synthesise(self, text: str, language: str = "en",
                   output_path: str = "response.mp3") -> Dict:
        if not GTTS_AVAILABLE:
            raise RuntimeError(
                "gTTS is not installed. Install with: pip install gTTS"
            )
        lang_code = _GTTS_LANG_MAP.get(language, "en")
        tts = _gTTS(text=text, lang=lang_code, slow=False)
        _ensure_dir(output_path)
        # gTTS produces MP3; rename if caller wants .wav but accept .mp3 too.
        save_path = output_path
        if output_path.endswith(".wav"):
            save_path = output_path.replace(".wav", ".mp3")
        tts.save(save_path)

        result = {
            "audio_path": save_path,
            "language": language,
            "tts_language": lang_code,
            "source": self.source,
            "format": "mp3",
            "rw_tts_note": _RW_TTS_NOTE if language == "rw" else None,
        }
        return result


# ── pyttsx3 backend ───────────────────────────────────────────────────────────
class Pyttsx3TTS:
    """Offline TTS using pyttsx3 (uses OS built-in voices). No internet needed."""

    name = "pyttsx3"
    source = "real-pyttsx3"

    def synthesise(self, text: str, language: str = "en",
                   output_path: str = "response.wav") -> Dict:
        if not PYTTSX3_AVAILABLE:
            raise RuntimeError(
                "pyttsx3 is not installed. Install with: pip install pyttsx3"
            )
        engine = _pyttsx3.init()
        engine.setProperty("rate", 150)   # speaking rate (words/min)

        _ensure_dir(output_path)
        save_path = output_path if output_path.endswith(".wav") else output_path + ".wav"
        engine.save_to_file(text, save_path)
        engine.runAndWait()

        return {
            "audio_path": save_path,
            "language": language,
            "tts_language": "en",   # OS likely only has English voice
            "source": self.source,
            "format": "wav",
            "rw_tts_note": _RW_TTS_NOTE if language == "rw" else None,
        }


# ── Stub backend ──────────────────────────────────────────────────────────────
def _write_silent_wav(path: str, duration_sec: float = 1.0,
                      sample_rate: int = 16000) -> str:
    """Write a minimal silent WAV file so the pipeline always produces a path."""
    _ensure_dir(path)
    n_samples = int(sample_rate * duration_sec)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{n_samples}h", *([0] * n_samples)))
    return path


class StubTTS:
    """Deterministic SIMULATED TTS — always available, clearly labelled.

    Writes a silent WAV file. The pipeline always produces an audio_path
    without crashing. ``source = "stub-simulated"`` is never confused with
    real speech output.
    """

    name = "stub"
    source = "stub-simulated"

    def synthesise(self, text: str, language: str = "en",
                   output_path: str = "response.wav") -> Dict:
        save_path = output_path if output_path.endswith(".wav") else output_path + ".wav"
        _write_silent_wav(save_path)
        return {
            "audio_path": save_path,
            "language": language,
            "tts_language": "stub",
            "source": self.source,
            "format": "wav",
            "rw_tts_note": _RW_TTS_NOTE if language == "rw" else None,
            "note": (
                "SIMULATED audio — silent WAV placeholder. "
                "Install gTTS (pip install gTTS) for real speech synthesis."
            ),
        }


# ── Backend selection + public API ────────────────────────────────────────────
def get_tts_backend(prefer: str = "gtts"):
    """Select the best available TTS backend.

    prefer: "gtts" (default) | "pyttsx3"
    Falls back down the chain: preferred → other real → stub.
    """
    if prefer == "gtts":
        if GTTS_AVAILABLE:
            return GttsTTS()
        if PYTTSX3_AVAILABLE:
            return Pyttsx3TTS()
    if prefer == "pyttsx3":
        if PYTTSX3_AVAILABLE:
            return Pyttsx3TTS()
        if GTTS_AVAILABLE:
            return GttsTTS()
    return StubTTS()


def tts_available() -> bool:
    return GTTS_AVAILABLE or PYTTSX3_AVAILABLE


def text_to_speech(
    text: str,
    language: str = "en",
    output_path: str = "response.mp3",
    prefer: str = "gtts",
) -> Dict:
    """Convert text to spoken audio.

    This is the public function called by voice_assistant.py.

    Args:
        text:        the text to speak (AI-generated agricultural answer).
        language:    "en" or "rw". Note: Kinyarwanda TTS falls back to English
                     voice — see module docstring for the honest limitation.
        output_path: where to save the audio file (.mp3 for gTTS, .wav for pyttsx3).
        prefer:      "gtts" (default) or "pyttsx3".

    Returns:
        dict: audio_path, language, tts_language, source, format, rw_tts_note.
    """
    backend = get_tts_backend(prefer=prefer)
    return backend.synthesise(text, language=language, output_path=output_path)
