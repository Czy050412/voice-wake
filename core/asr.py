# -*- coding: utf-8 -*-
"""
ASR Engine v3 — Dual-model, in-memory, streaming-optimized.
- Tiny model for wake word & pre-filtering (fast, always-on)
- Small model for full command recognition (accurate, on-demand)
- Zero temp files: in-memory WAV → direct bytes streaming
"""
import io
import os
import wave
import time
import logging
from typing import Optional, Generator

logger = logging.getLogger("voice_wake.asr")

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WHISPER_CACHE = os.path.join(APP_DIR, ".whisper_cache")

# Model instances (singletons)
_tiny_model = None
_small_model = None


def _load_model(size: str, device="cpu", compute="int8"):
    """Load a faster-whisper model. Cached per size."""
    from faster_whisper import WhisperModel
    return WhisperModel(
        size, device=device, compute_type=compute,
        download_root=WHISPER_CACHE,
        cpu_threads=4,  # Optimal for most CPUs
        num_workers=2,
    )


def init_tiny():
    """Load tiny model (~75MB). Used for continuous wake-word pre-filter."""
    global _tiny_model
    if _tiny_model is not None:
        return _tiny_model
    t0 = time.time()
    logger.info("Loading tiny model...")
    _tiny_model = _load_model("tiny", device="cpu", compute="int8")
    logger.info(f"Tiny model ready ({time.time()-t0:.1f}s)")
    return _tiny_model


def init_small():
    """Load small model (~500MB). Used for accurate command recognition."""
    global _small_model
    if _small_model is not None:
        return _small_model
    t0 = time.time()
    logger.info("Loading small model...")
    _small_model = _load_model("small", device="cpu", compute="int8")
    logger.info(f"Small model ready ({time.time()-t0:.1f}s)")
    return _small_model


def prewarm():
    """Pre-load both models. ~8s total, but eliminates cold-start latency."""
    init_tiny()
    init_small()
    # Run a dummy inference to warm up CTranslate2 cache
    _dummy_warmup(_tiny_model)
    _dummy_warmup(_small_model)


def _dummy_warmup(model):
    """Run a short silent audio through the model to warm caches."""
    import numpy as np
    dummy = np.zeros(16000, dtype=np.float32)  # 1 second of silence
    wav_bytes = _float32_to_wav_bytes(dummy, 16000)
    try:
        list(model.transcribe(wav_bytes, language="zh"))
    except:
        pass


# ---- In-memory WAV conversion (zero temp files!) ----

def _float32_to_wav_bytes(audio: "np.ndarray", sample_rate: int) -> bytes:
    """Convert float32 numpy array to WAV bytes in memory. Zero disk I/O."""
    import numpy as np
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)      # int16 = 2 bytes
        wf.setframerate(sample_rate)
        # Convert float32 [-1,1] → int16 [-32768,32767]
        int_data = (audio * 32767).astype(np.int16)
        wf.writeframes(int_data.tobytes())
    return buf.getvalue()


def recognize(audio_data, use_small: bool = False, language: str = "zh") -> str:
    """
    Recognize speech from SpeechRecognition AudioData.
    Uses in-memory WAV → direct bytes pass to faster-whisper.

    Args:
        audio_data: SpeechRecognition AudioData object
        use_small: True = use small model (more accurate), False = use tiny
        language: "zh" or "en"
    """
    model = _small_model if (use_small and _small_model is not None) else _tiny_model
    if model is None:
        model = init_tiny()  # Fallback

    # Convert to raw audio samples (float32 numpy array)
    import numpy as np
    raw = audio_data.get_raw_data()
    sample_rate = audio_data.sample_rate
    audio_np = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

    # Convert to WAV bytes in-memory (NO TEMP FILES!)
    wav_bytes = _float32_to_wav_bytes(audio_np, sample_rate)

    try:
        segments, _ = model.transcribe(
            wav_bytes, language=language, beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=300),
        )
        texts = [s.text.strip() for s in segments]
        return "".join(texts)
    except Exception as e:
        logger.error(f"ASR error: {e}")
        return ""


def recognize_streaming(audio_data, language="zh") -> Generator:
    """Generator-based streaming recognition. Yields partial results as they arrive."""
    model = _small_model or _tiny_model
    if model is None:
        model = init_tiny()

    import numpy as np
    raw = audio_data.get_raw_data()
    sample_rate = audio_data.sample_rate
    audio_np = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    wav_bytes = _float32_to_wav_bytes(audio_np, sample_rate)

    try:
        segments, _ = model.transcribe(
            wav_bytes, language=language, beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=300),
        )
        for seg in segments:
            yield seg.text.strip()
    except Exception as e:
        logger.error(f"Streaming ASR error: {e}")
        yield ""
