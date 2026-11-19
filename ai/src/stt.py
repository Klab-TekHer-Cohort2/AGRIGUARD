"""Speech-to-Text (STT) for AgriGuard voice input.

Converts a farmer's spoken audio to text so it can be processed by the same
agricultural AI pipeline that handles typed text.

TWO BACKENDS — clearly distinguished:

1. ``WhisperSTT`` — REAL speech recognition using OpenAI Whisper
   (openai-whisper package, runs fully offline on CPU/GPU, no API key).
   - Supports 99 languages including English.
   - Kinyarwanda (rw) support: Whisper includes Kinyarwanda in its training
     data but recognition quality for Kinyarwanda agricultural vocabulary has
     NOT been validated in Rwandan field conditions. Treat output as a best
     effort — always show the transcription to the farmer for confirmation.
   - Model sizes: tiny (fastest, Colab-friendly), base, small, medium, large.
     Recommended for Colab demos: "base" (140 MB, good accuracy/speed balance).

2. ``StubSTT`` — deterministic fallback when openai-whisper is not installed.
   Returns clearly labelled SIMULATED transcriptions. This exists so the voice
   pipeline always demonstrates the full flow even without the STT dependency.
   The stub output is always tagged ``source = "stub-simulated"`` so callers
   can never mistake it for real speech recognition.

KINYARWANDA LIMITATION (honest documentation):
   - No dedicated Kinyarwanda ASR model is freely available as of 2024.
   - Whisper's Kinyarwanda quality depends heavily on audio quality and accent.
   - For production use, evaluate Whisper-large-v3 on Rwandan field recordings.
   - Mozilla Common Voice has a small Kinyarwanda dataset that could be used to
     fine-tune Whisper: https://commonvoice.mozilla.org/rw

INSTALL (Colab):
   pip install openai-whisper
   # Also requires ffmpeg:
   apt-get install -y ffmpeg    (Colab) or brew install ffmpeg (macOS)

API KEY: None required. Whisper runs fully locally.
"""

import os
from typing import Dict, Optional

# ── Detect Whisper ────────────────────────────────────────────────────────────
try:
    import whisper as _whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


# ── Whisper language code map ─────────────────────────────────────────────────
# Whisper uses ISO 639-1 two-letter codes. "rw" is Kinyarwanda.
LANGUAGE_CODE_MAP = {
    "en": "en",
    "rw": "rw",    # Kinyarwanda — Whisper supports it (quality varies)
    "auto": None,  # None = Whisper auto-detects
}

# Demo stub transcriptions — used when Whisper is not installed.
_STUB_TRANSCRIPTIONS = {
    "en": {
        "default": "What should I do if my maize leaves have holes and there are insects?",
        "armyworm": "The leaves of my maize have holes and I can see small insects near the whorl.",
        "unknown":  "Something strange is happening with my plants, I am not sure what it is.",
        "help":     "I need help, I want an agronomist to look at my field.",
        "yellow":   "My maize leaves are turning yellow, what should I do?",
    },
    "rw": {
        "default": "Ibigori byanjye birimo gukangarwa n'udukoko, mbwira inama.",
        "armyworm": "Ibibabi by'ibigori byanjye birahinduka kandi hari imyanya myinshi.",
        "unknown":  "Hari ikibazo ku bimera byanjye, sinzi uko bimeze neza.",
        "help":     "Ndashaka umuhinzi w'ubuhinzi kuza kureba umurima wanjye.",
        "yellow":   "Ibibabi by'ibigori byanjye birahinduka umuhondo.",
    },
}


class WhisperSTT:
    """Real offline STT using OpenAI Whisper (openai-whisper package).

    Attributes:
        model_name: Whisper model size. "base" is recommended for Colab.
                    Options: tiny, base, small, medium, large, large-v2, large-v3
        device: "cpu" or "cuda". Colab free tier supports "cuda" when GPU is on.
    """

    name = "whisper"
    source = "real-whisper"

    # Supported sizes, documented for reference.
    MODEL_INFO = {
        "tiny":     {"params": "39M",  "colab_ok": True,  "rw_quality": "low"},
        "base":     {"params": "74M",  "colab_ok": True,  "rw_quality": "medium"},
        "small":    {"params": "244M", "colab_ok": True,  "rw_quality": "medium"},
        "medium":   {"params": "769M", "colab_ok": True,  "rw_quality": "good"},
        "large":    {"params": "1550M","colab_ok": False, "rw_quality": "best"},
        "large-v3": {"params": "1550M","colab_ok": False, "rw_quality": "best"},
    }

    def __init__(self, model_name: str = "base", device: str = "cpu"):
        if not WHISPER_AVAILABLE:
            raise RuntimeError(
                "openai-whisper is not installed.\n"
                "Install with:  pip install openai-whisper\n"
                "Also install ffmpeg:  apt-get install -y ffmpeg"
            )
        self.model_name = model_name
        self.device = device
        self._model = None

    def _load(self):
        if self._model is None:
            self._model = _whisper.load_model(self.model_name, device=self.device)

    def transcribe(self, audio_path: str, language: str = "auto") -> Dict:
        """Transcribe an audio file.

        Args:
            audio_path: path to a WAV / MP3 / M4A / FLAC / OGG file.
            language: "en", "rw", or "auto" (Whisper detects automatically).

        Returns:
            dict with keys: text, language, confidence, segments, source.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self._load()
        lang_code = LANGUAGE_CODE_MAP.get(language)   # None = auto-detect
        options = {"language": lang_code} if lang_code else {}
        result = self._model.transcribe(audio_path, **options)

        # Whisper does not return a single confidence score; we approximate from
        # the average log-probability of segments (higher is more confident).
        segments = result.get("segments", [])
        if segments:
            avg_logprob = sum(s.get("avg_logprob", -1.0) for s in segments) / len(segments)
            # Map log-prob (typically -0.1 to -1.5) to 0–1 range.
            confidence = float(max(0.0, min(1.0, 1.0 + avg_logprob / 2.0)))
        else:
            confidence = 0.5

        detected_lang = result.get("language", language)

        return {
            "text": result["text"].strip(),
            "language": detected_lang,
            "confidence": round(confidence, 2),
            "segments": [
                {"start": s["start"], "end": s["end"], "text": s["text"]}
                for s in segments
            ],
            "source": self.source,
            "model": self.model_name,
            "note": (
                "Kinyarwanda (rw) recognition quality has not been validated "
                "in Rwandan field conditions. Treat output as best-effort."
                if detected_lang == "rw" else None
            ),
        }


class StubSTT:
    """Deterministic SIMULATED STT — always available, clearly labelled.

    Returns fixed transcriptions so the full voice pipeline can be demonstrated
    without installing openai-whisper or having a real audio file. The stub
    makes it obvious it is not real recognition: ``source = "stub-simulated"``.
    """

    name = "stub"
    source = "stub-simulated"   # never confused with real Whisper output

    def transcribe(self, audio_path: str, language: str = "auto") -> Dict:
        """Return a deterministic demo transcription based on the filename."""
        lang = language if language in ("en", "rw") else "en"
        filename = os.path.basename(audio_path or "").lower()

        # Pick a transcription based on filename keywords.
        bank = _STUB_TRANSCRIPTIONS[lang]
        text = bank["default"]
        for keyword in ("armyworm", "unknown", "help", "yellow"):
            if keyword in filename:
                text = bank[keyword]
                break

        return {
            "text": text,
            "language": lang,
            "confidence": 0.72,   # fixed placeholder
            "segments": [],
            "source": self.source,
            "model": "stub",
            "note": (
                "SIMULATED transcription — not real speech recognition. "
                "Install openai-whisper for real STT."
            ),
        }


# ── Module-level singleton + public API ──────────────────────────────────────
_WHISPER_INSTANCE: Optional[WhisperSTT] = None


def load_whisper(model_name: str = "base", device: str = "cpu") -> WhisperSTT:
    """Load (and cache) the Whisper model. Call once before transcribing."""
    global _WHISPER_INSTANCE
    _WHISPER_INSTANCE = WhisperSTT(model_name=model_name, device=device)
    _WHISPER_INSTANCE._load()   # preload the model weights
    return _WHISPER_INSTANCE


def get_stt_backend(use_real: bool = True):
    """Return the active STT backend: Whisper if loaded/available, else Stub."""
    if use_real and WHISPER_AVAILABLE and _WHISPER_INSTANCE is not None:
        return _WHISPER_INSTANCE
    if use_real and WHISPER_AVAILABLE and _WHISPER_INSTANCE is None:
        # Auto-load with the lightest model so the first call just works.
        return WhisperSTT(model_name="base")
    return StubSTT()


def speech_to_text(
    audio_path: str,
    language: str = "auto",
    use_real: bool = True,
) -> Dict:
    """Convert an audio file to text.

    This is the public function called by voice_assistant.py.

    Args:
        audio_path: path to WAV / MP3 / M4A / FLAC / OGG file.
                    In Colab use the uploaded file path.
        language:   "en", "rw", or "auto" (auto-detect).
        use_real:   True → use Whisper if available, else Stub.
                    False → always use the Stub (for testing).

    Returns:
        dict: text, language, confidence, segments, source, model, note.
    """
    backend = get_stt_backend(use_real=use_real)
    return backend.transcribe(audio_path, language=language)
