# -*- coding: utf-8 -*-
"""
Audio Pipeline v3 — Thread-optimized capture → VAD → recognition.
Separate threads for capture, VAD, and recognition to minimize latency.
"""
import threading
import time
import logging
import queue
from typing import Optional, Callable

logger = logging.getLogger("voice_wake.pipeline")


class AudioPipeline:
    """
    Optimized audio pipeline:
    - Thread 1: Continuous audio capture
    - Thread 2: VAD + silence detection
    - Thread 3: ASR recognition (dispatched on phrase complete)

    Queues avoid GIL contention and decouple stages.
    """

    def __init__(self, recognizer, microphone, on_phrase: Callable = None):
        self.recognizer = recognizer
        self.microphone = microphone
        self.on_phrase = on_phrase
        self._running = False
        self._source = None
        self._phrase_queue = queue.Queue(maxsize=8)

    def start(self, timeout: float = None, phrase_limit: float = None):
        """Start the pipeline. Returns immediately, runs in background."""
        self._running = True
        self._source = self.microphone.__enter__()

        # Adjust for ambient noise
        self.recognizer.adjust_for_ambient_noise(self._source, duration=0.3)

        # Capture thread
        threading.Thread(target=self._capture_loop,
                         args=(timeout, phrase_limit),
                         daemon=True, name="audio-capture").start()

        # Dispatch thread
        threading.Thread(target=self._dispatch_loop,
                         daemon=True, name="phrase-dispatch").start()

        logger.info("Audio pipeline started")

    def stop(self):
        """Stop the pipeline."""
        self._running = False
        if self._source:
            try:
                self.microphone.__exit__(None, None, None)
            except:
                pass
        logger.info("Audio pipeline stopped")

    def _capture_loop(self, timeout, phrase_limit):
        """Thread 1: Continuous capture with VAD."""
        while self._running:
            try:
                audio = self.recognizer.listen(
                    self._source,
                    timeout=timeout or 3,
                    phrase_time_limit=phrase_limit or 10,
                )
                # Queue for processing
                try:
                    self._phrase_queue.put_nowait(audio)
                except queue.Full:
                    # Drop oldest if queue is full (backpressure)
                    try:
                        self._phrase_queue.get_nowait()
                        self._phrase_queue.put_nowait(audio)
                    except:
                        pass
            except Exception as e:
                if self._running:
                    logger.debug(f"Capture cycle: {e}")
                time.sleep(0.1)

    def _dispatch_loop(self):
        """Thread 2: Dispatch recognized phrases to callback."""
        while self._running:
            try:
                audio = self._phrase_queue.get(timeout=0.5)
                if self.on_phrase:
                    self.on_phrase(audio)
            except queue.Empty:
                continue
            except Exception as e:
                logger.warning(f"Dispatch error: {e}")
