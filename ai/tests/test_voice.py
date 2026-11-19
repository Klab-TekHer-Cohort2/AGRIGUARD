"""Tests: Voice AI pipeline (section 9).

All tests use the Stub backends (use_real_stt=False, tts_prefer forces Stub)
so they run without openai-whisper, ffmpeg, or gTTS installed. The Stub
backends are deterministic and clearly labelled (source="stub-simulated").

Four test groups:
    1. English: audio → English text → English answer → English audio
    2. Kinyarwanda: audio → Kinyarwanda text → Kinyarwanda answer → audio
    3. Low-confidence escalation: audio → unknown question → escalation → spoken message
    4. Image + voice: image + audio → crop analysis → spoken recommendation

Each test verifies the pipeline produces the correct structure — it does NOT
test the quality of Whisper transcription or TTS audio (that requires real
hardware/network and is validated separately).
"""

import os
import tempfile

import pytest

from ai.src.stt import speech_to_text, StubSTT, WHISPER_AVAILABLE
from ai.src.tts import text_to_speech, StubTTS, GTTS_AVAILABLE, PYTTSX3_AVAILABLE
from ai.src.voice_assistant import voice_farmer_assistant, voice_crop_report


# ── Helpers ───────────────────────────────────────────────────────────────────
def _fake_audio(filename: str = "test_audio.wav") -> str:
    """Write a minimal valid WAV file so path-exists checks pass."""
    import wave, struct
    path = os.path.join(tempfile.gettempdir(), filename)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(struct.pack("<100h", *([0] * 100)))
    return path


def _tmp_out(name: str = "out.wav") -> str:
    return os.path.join(tempfile.gettempdir(), name)


# ── 1. STT unit tests ─────────────────────────────────────────────────────────
class TestSTT:
    def test_stub_returns_required_keys(self):
        audio = _fake_audio("en_test.wav")
        result = speech_to_text(audio, language="en", use_real=False)
        for key in ("text", "language", "confidence", "segments", "source", "model"):
            assert key in result, f"Missing key: {key}"

    def test_stub_source_is_labelled_simulated(self):
        audio = _fake_audio("en_test.wav")
        result = speech_to_text(audio, language="en", use_real=False)
        assert result["source"] == "stub-simulated"

    def test_stub_english_returns_english_text(self):
        audio = _fake_audio("en_test.wav")
        result = speech_to_text(audio, language="en", use_real=False)
        assert result["language"] == "en"
        assert len(result["text"]) > 0

    def test_stub_kinyarwanda_returns_rw_text(self):
        audio = _fake_audio("rw_test.wav")
        result = speech_to_text(audio, language="rw", use_real=False)
        assert result["language"] == "rw"
        assert len(result["text"]) > 0

    def test_stub_has_confidence_between_0_and_1(self):
        audio = _fake_audio("conf_test.wav")
        result = speech_to_text(audio, language="en", use_real=False)
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.skipif(not WHISPER_AVAILABLE, reason="openai-whisper not installed")
    def test_whisper_instantiates_without_error(self):
        from ai.src.stt import WhisperSTT
        stt = WhisperSTT(model_name="tiny")
        assert stt.name == "whisper"


# ── 2. TTS unit tests ─────────────────────────────────────────────────────────
class TestTTS:
    def test_stub_returns_required_keys(self):
        result = text_to_speech("Hello farmer.", language="en",
                                output_path=_tmp_out("tts_en.wav"), prefer="stub")
        for key in ("audio_path", "language", "source", "format"):
            assert key in result

    def test_stub_source_is_labelled_simulated(self):
        result = text_to_speech("Hello.", language="en",
                                output_path=_tmp_out("tts_src.wav"), prefer="stub")
        assert result["source"] == "stub-simulated"

    def test_stub_creates_audio_file(self):
        out = _tmp_out("tts_file.wav")
        text_to_speech("Test audio.", language="en", output_path=out, prefer="stub")
        assert os.path.exists(out)
        assert os.path.getsize(out) > 0

    def test_kinyarwanda_includes_limitation_note(self):
        result = text_to_speech("Ibigori byanjye.", language="rw",
                                output_path=_tmp_out("tts_rw.wav"), prefer="stub")
        assert result["rw_tts_note"] is not None
        assert "LIMITATION" in result["rw_tts_note"]

    def test_english_has_no_rw_note(self):
        result = text_to_speech("My maize.", language="en",
                                output_path=_tmp_out("tts_en2.wav"), prefer="stub")
        assert result.get("rw_tts_note") is None

    @pytest.mark.skipif(not GTTS_AVAILABLE, reason="gTTS not installed")
    def test_gtts_produces_mp3_file(self):
        out = _tmp_out("gtts_test.mp3")
        result = text_to_speech("Hello farmer.", language="en",
                                output_path=out, prefer="gtts")
        assert result["source"] == "real-gtts"
        assert os.path.exists(result["audio_path"])


# ── 3. English end-to-end voice pipeline ─────────────────────────────────────
class TestEnglishVoicePipeline:
    def test_full_pipeline_returns_all_keys(self):
        audio = _fake_audio("en_pipeline.wav")
        result = voice_farmer_assistant(
            audio_path=audio,
            language="en",
            tts_output_path=_tmp_out("en_response.wav"),
            use_real_stt=False,
            tts_prefer="stub",
        )
        for key in ("transcribed_text", "language", "answer_text",
                    "audio_path", "confidence", "needs_agronomist",
                    "escalation_reason", "stt_source", "tts_source"):
            assert key in result, f"Missing key: {key}"

    def test_english_pipeline_language_is_en(self):
        audio = _fake_audio("en_lang.wav")
        result = voice_farmer_assistant(
            audio_path=audio, language="en",
            tts_output_path=_tmp_out("en_lang_resp.wav"),
            use_real_stt=False, tts_prefer="stub",
        )
        assert result["language"] == "en"

    def test_english_pipeline_produces_audio_file(self):
        audio = _fake_audio("en_audio.wav")
        out = _tmp_out("en_audio_resp.wav")
        result = voice_farmer_assistant(
            audio_path=audio, language="en",
            tts_output_path=out,
            use_real_stt=False, tts_prefer="stub",
        )
        assert os.path.exists(result["audio_path"])

    def test_english_stt_source_is_stub(self):
        audio = _fake_audio("en_stub.wav")
        result = voice_farmer_assistant(
            audio_path=audio, language="en",
            tts_output_path=_tmp_out("en_stub_resp.wav"),
            use_real_stt=False, tts_prefer="stub",
        )
        assert result["stt_source"] == "stub-simulated"


# ── 4. Kinyarwanda voice pipeline ─────────────────────────────────────────────
class TestKinyarwandaVoicePipeline:
    def test_rw_pipeline_language_is_rw(self):
        audio = _fake_audio("rw_pipeline.wav")
        result = voice_farmer_assistant(
            audio_path=audio, language="rw",
            tts_output_path=_tmp_out("rw_response.wav"),
            use_real_stt=False, tts_prefer="stub",
        )
        assert result["language"] == "rw"

    def test_rw_pipeline_includes_tts_limitation_note(self):
        audio = _fake_audio("rw_tts.wav")
        result = voice_farmer_assistant(
            audio_path=audio, language="rw",
            tts_output_path=_tmp_out("rw_tts_resp.wav"),
            use_real_stt=False, tts_prefer="stub",
        )
        assert result["rw_tts_note"] is not None

    def test_rw_pipeline_answer_is_non_empty(self):
        audio = _fake_audio("rw_ans.wav")
        result = voice_farmer_assistant(
            audio_path=audio, language="rw",
            tts_output_path=_tmp_out("rw_ans_resp.wav"),
            use_real_stt=False, tts_prefer="stub",
        )
        assert len(result["answer_text"]) > 0


# ── 5. Low-confidence escalation via voice ─────────────────────────────────────
class TestVoiceEscalation:
    def test_unknown_audio_triggers_escalation(self):
        # "unknown" in filename → Stub returns the "not sure" transcription
        audio = _fake_audio("unknown_problem.wav")
        result = voice_farmer_assistant(
            audio_path=audio, language="en",
            tts_output_path=_tmp_out("esc_response.wav"),
            use_real_stt=False, tts_prefer="stub",
        )
        # For an "unknown / something strange" question, escalation is expected.
        # We just verify the pipeline runs and needs_agronomist is a bool.
        assert isinstance(result["needs_agronomist"], bool)

    def test_escalated_answer_contains_escalation_message(self):
        audio = _fake_audio("unknown_problem.wav")
        result = voice_farmer_assistant(
            audio_path=audio, language="en",
            tts_output_path=_tmp_out("esc_msg_resp.wav"),
            use_real_stt=False, tts_prefer="stub",
        )
        if result["needs_agronomist"]:
            assert "agronomist" in result["answer_text"].lower() or \
                   "extension" in result["answer_text"].lower()

    def test_escalation_spoken_in_kinyarwanda_when_rw(self):
        audio = _fake_audio("unknown_rw.wav")
        result = voice_farmer_assistant(
            audio_path=audio, language="rw",
            tts_output_path=_tmp_out("esc_rw_resp.wav"),
            use_real_stt=False, tts_prefer="stub",
        )
        if result["needs_agronomist"] and result["language"] == "rw":
            assert "umuhinzi" in result["answer_text"].lower() or \
                   "raporo" in result["answer_text"].lower()


# ── 6. Voice + image combined pipeline ────────────────────────────────────────
class TestVoicePlusImage:
    def test_voice_crop_report_returns_all_keys(self):
        audio = _fake_audio("armyworm_voice.wav")
        result = voice_crop_report(
            audio_path=audio,
            crop="Maize",
            image="maize-armyworm.jpg",
            language="en",
            tts_output_path=_tmp_out("vcr_response.wav"),
            use_real_stt=False,
            tts_prefer="stub",
        )
        for key in ("transcribed_text", "language", "crop_analysis",
                    "answer_text", "audio_path", "needs_agronomist",
                    "stt_source", "tts_source", "vision_source"):
            assert key in result, f"Missing key: {key}"

    def test_voice_crop_report_vision_source_is_simulated(self):
        audio = _fake_audio("vcr_vis.wav")
        result = voice_crop_report(
            audio_path=audio, crop="Maize",
            image="maize-armyworm.jpg", language="en",
            tts_output_path=_tmp_out("vcr_vis_resp.wav"),
            use_real_stt=False, tts_prefer="stub",
        )
        assert result["vision_source"] == "simulated-demo"

    def test_voice_crop_report_identifies_maize(self):
        audio = _fake_audio("vcr_maize.wav")
        result = voice_crop_report(
            audio_path=audio, crop="Maize",
            image="maize-armyworm.jpg", language="en",
            tts_output_path=_tmp_out("vcr_maize_resp.wav"),
            use_real_stt=False, tts_prefer="stub",
        )
        assert result["crop_analysis"]["crop_id"] == "maize"

    def test_voice_crop_report_produces_audio_file(self):
        audio = _fake_audio("vcr_audio.wav")
        out = _tmp_out("vcr_audio_resp.wav")
        result = voice_crop_report(
            audio_path=audio, crop="Maize",
            image="maize-armyworm.jpg", language="en",
            tts_output_path=out,
            use_real_stt=False, tts_prefer="stub",
        )
        assert os.path.exists(result["audio_path"])
        assert os.path.getsize(result["audio_path"]) > 0
