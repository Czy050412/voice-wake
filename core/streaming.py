# -*- coding: utf-8 -*-
"""
Streaming ASR — True real-time speech-to-text via sliding window.
Chunks audio continuously, transcribes each chunk, deduplicates overlaps.

┌───────── chunk 0~2s ─────────┐
              ┌──overlap 1.5~2s──┐
              ┌───────── chunk 1.5~3.5s ─────────┐
                                   ┌──overlap 3~3.5s──┐
                                   ┌───────── chunk 3~5s ─────────┐

Each chunk → tiny model (~0.3s latency) → dedup → yield new text.
Perceived as real-time: ~1.5s lag, 30-50ms chunks.
"""
import io
import os
import wave
import time
import logging
import threading
import numpy as np
from collections import deque
from typing import Generator, Optional, Callable

logger = logging.getLogger("voice_wake.streaming")

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Import from local asr module
from .asr import init_tiny, init_small, _float32_to_wav_bytes

CHUNK_SECONDS = 2.0       # Transcribe window size
OVERLAP_SECONDS = 0.5     # Overlap between windows (for dedup seam)
STEP_SECONDS = CHUNK_SECONDS - OVERLAP_SECONDS  # 1.5s = how often we run
SAMPLE_RATE = 16000


def _dedup_text(prev: str, current: str) -> str:
    """
    Deduplicate overlapping text between consecutive chunks.
    Finds the longest suffix of `prev` that is a prefix of `current`, removes it.
    """
    if not prev or not current:
        return current
    # Find common overlap: try decreasing suffix lengths
    max_overlap = min(len(prev), len(current), 20)  # Max 20 chars overlap
    for n in range(max_overlap, 2, -1):
        if prev[-n:] == current[:n]:
            return current[n:]
    return current


class StreamingRecognizer:
    """
    Sliding-window recognizer. Feed raw audio frames, get text as it arrives.
    Runs transcription in a background thread to avoid blocking capture.
    """

    def __init__(self, language: str = "zh", model_size: str = "tiny",
                 on_result: Callable = None):
        self.language = language
        try:
            self.model = init_tiny()  # tiny = fast enough for streaming
        except Exception:
            logger.warning("Tiny model unavailable, falling back to small")
            try:
                self.model = init_small()
            except Exception:
                logger.warning("Small also fails, trying tiny with no cache check")
                self.model = init_tiny()
        self.on_result = on_result
        self._buffer = np.array([], dtype=np.float32)
        self._prev_text = ""
        self._full_text = ""
        self._running = False
        self._lock = threading.Lock()
        self._result_queue = deque(maxlen=64)
        self._worker = None

    def start(self):
        """Start background transcription worker."""
        self._running = True
        self._worker = threading.Thread(target=self._transcribe_loop, daemon=True, name="stream-asr")
        self._worker.start()
        logger.info("Streaming ASR started (chunk=%.1fs, step=%.1fs)", CHUNK_SECONDS, STEP_SECONDS)

    def stop(self) -> str:
        """Stop streaming and return final accumulated text."""
        self._running = False
        # Transcribe any remaining audio
        if len(self._buffer) > SAMPLE_RATE * 0.3:  # At least 0.3s left
            text = self._transcribe_chunk(self._buffer)
            new = _dedup_text(self._prev_text, text)
            if new:
                self._full_text += new
        return self._full_text.strip()

    def feed(self, audio_chunk: np.ndarray):
        """
        Feed raw float32 audio samples. Thread-safe.
        audio_chunk: float32 numpy array [-1.0, 1.0] at 16kHz.
        """
        if not self._running:
            return
        with self._lock:
            self._buffer = np.concatenate([self._buffer, audio_chunk])

    @property
    def partial_text(self) -> str:
        """Current accumulated text so far."""
        return self._full_text.strip()

    @property
    def buffer_seconds(self) -> float:
        with self._lock:
            return len(self._buffer) / SAMPLE_RATE

    def _transcribe_loop(self):
        """Background worker: periodically transcribes buffered audio."""
        while self._running:
            time.sleep(STEP_SECONDS * 0.6)  # Run slightly faster than step to reduce latency

            with self._lock:
                buf_len = len(self._buffer)
                chunk_samples = int(CHUNK_SECONDS * SAMPLE_RATE)

            if buf_len < chunk_samples:
                continue  # Not enough audio yet

            with self._lock:
                chunk = self._buffer[:chunk_samples].copy()
                self._buffer = self._buffer[int(STEP_SECONDS * SAMPLE_RATE):]

            # Transcribe in background
            try:
                text = self._transcribe_chunk(chunk)
                new = _dedup_text(self._prev_text, text)
                self._prev_text = text
                if new:
                    self._full_text += new
                    self._result_queue.append(new)
                    if self.on_result:
                        self.on_result(new, self._full_text)
                    logger.debug("Stream: +'%s' | total='%s'", new[:30], self._full_text[-60:])
            except Exception as e:
                logger.warning("Stream chunk error: %s", e)

    def _transcribe_chunk(self, audio: np.ndarray) -> str:
        """Transcribe a single chunk of audio and return text."""
        if len(audio) < SAMPLE_RATE * 0.2:  # Skip <200ms
            return ""

        wav_bytes = _float32_to_wav_bytes(audio, SAMPLE_RATE)

        try:
            segments, _ = self.model.transcribe(
                wav_bytes, language=self.language, beam_size=5,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=200,
                    speech_pad_ms=100,
                ),
                condition_on_previous_text=False,  # Each chunk independent
            )
            return "".join(s.text.strip() for s in segments)
        except Exception as e:
            logger.warning("Transcribe error: %s", e)
            return ""


def test_streaming(source_file: str = None):
    """
    Test streaming with a WAV file or live mic.
    Usage: python -m core.streaming [audio.wav]
    """
    if source_file and os.path.exists(source_file):
        import wave as wv
        with wv.open(source_file, 'rb') as wf:
            assert wf.getnchannels() == 1
            assert wf.getframerate() == SAMPLE_RATE
            frames = wf.readframes(wf.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

        # Simulate streaming
        import sys
        sys.path.insert(0, APP_DIR)
        r = StreamingRecognizer(language="zh")
        r.start()

        chunk_size = SAMPLE_RATE // 10  # 100ms chunks
        for i in range(0, len(audio), chunk_size):
            r.feed(audio[i:i+chunk_size])
            time.sleep(0.1)
            partial = r.partial_text
            if partial:
                print(f"\r[Live] {partial}", end="")

        final = r.stop()
        print(f"\n[Final] {final}")
    else:
        # Live mic test
        import speech_recognition as sr
        import sys
        sys.path.insert(0, os.path.dirname(APP_DIR))

        r = StreamingRecognizer(language="zh")
        r.start()

        def on_partial(new, full):
            print(f"[{time.time():.0f}] {full[-80:]}")

        r.on_result = on_partial

        rec = sr.Recognizer()
        rec.energy_threshold = 300
        rec.dynamic_energy_threshold = False

        try:
            with sr.Microphone(sample_rate=SAMPLE_RATE) as source:
                print("Streaming live — speak now (Ctrl+C to stop)...")
                rec.adjust_for_ambient_noise(source, duration=0.5)
                while True:
                    try:
                        frame = source.stream.read(SAMPLE_RATE // 4)  # 250ms
                        audio_np = np.frombuffer(frame, dtype=np.int16).astype(np.float32) / 32768.0
                        r.feed(audio_np)
                    except KeyboardInterrupt:
                        break
        finally:
            final = r.stop()
            print(f"\n\n[Final] {final}")


if __name__ == "__main__":
    import sys
    test_streaming(sys.argv[1] if len(sys.argv) > 1 else None)
