# -*- coding: utf-8 -*-
"""
Voice Wake v3 "Jarvis" — Unlimited Voice Assistant
==================================================
- Pluggable action system: shell, HTTP, Python, keyboard, AI assistant
- Dual-model ASR: tiny for wake-word, small for commands
- In-memory WAV processing: zero temp files
- 🆕 Streaming mode: real-time sliding-window transcription
- Auto-detects any AI assistant: WorkBuddy, CodeBuddy, Cursor, Windsurf, DeepSeek, Kimi...
"""
import os
import sys
import time
import logging
import threading
import numpy as np

import speech_recognition as sr

# ---- Paths ----
APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)

# ---- Logging ----
LOG_FILE = os.path.join(APP_DIR, "voice_wake.log")
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("voice_wake")

OVERLAY_FILE = os.path.join(APP_DIR, "overlay_text.txt")


def overlay(tag, text):
    """Write status to transparent HUD overlay."""
    try:
        with open(OVERLAY_FILE, "w", encoding="utf-8") as f:
            f.write(f"[{tag}] {text}"[:200])
    except:
        pass


# ---- Config ----
WAKE_WORD = "狗蛋"
LANGUAGE = "zh"
MODEL_SIZE = "small"
ENERGY_THRESHOLD = 550
PAUSE_THRESHOLD = 0.6
PHRASE_LIMIT = 10
SEND_COOLDOWN = 3.0
DYNAMIC_ENERGY = False
PREWARM = True
DUAL_MODEL = True
STREAMING = True  # 🆕 Real-time streaming mode

_config = {}
try:
    import yaml
    cfg_path = os.path.join(APP_DIR, "config", "settings.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            _config = yaml.safe_load(f)
        if _config:
            WAKE_WORD = _config.get("wake_word", WAKE_WORD)
            LANGUAGE = _config.get("language", LANGUAGE)
            MODEL_SIZE = _config.get("model", MODEL_SIZE)
            audio = _config.get("audio", {})
            ENERGY_THRESHOLD = audio.get("energy_threshold", ENERGY_THRESHOLD)
            PAUSE_THRESHOLD = audio.get("pause_threshold", PAUSE_THRESHOLD)
            PHRASE_LIMIT = audio.get("phrase_limit", PHRASE_LIMIT)
            DYNAMIC_ENERGY = audio.get("dynamic_energy", DYNAMIC_ENERGY)
            perf = _config.get("performance", {})
            PREWARM = perf.get("prewarm", True)
            DUAL_MODEL = perf.get("dual_model", True)
            STREAMING = perf.get("streaming", True)
            SEND_COOLDOWN = _config.get("actions", {}).get("send_cooldown", SEND_COOLDOWN)
except Exception as e:
    log.warning(f"Config load failed: {e}")


# ---- ASR Engine ----
import core.asr
from core.asr import init_tiny, init_small, prewarm, recognize
from core.streaming import StreamingRecognizer, SAMPLE_RATE as STREAM_RATE


def init_models():
    """Load ASR models. Dual-model: tiny always-on + small on-demand."""
    log.info("Initializing ASR engines...")
    t0 = time.time()

    init_tiny()  # Always load tiny for wake-word detection
    if DUAL_MODEL:
        init_small()

    if PREWARM:
        prewarm()
        log.info(f"Models pre-warmed in {time.time()-t0:.1f}s")


# ---- Action Pipeline ----
from actions import action_registry, load_builtins


def init_actions():
    """Load built-in and custom actions."""
    load_builtins(action_registry, _config)

    # Also load from actions.yaml if present
    actions_yaml = os.path.join(APP_DIR, "config", "actions.yaml")
    if os.path.exists(actions_yaml):
        try:
            import yaml
            with open(actions_yaml, "r", encoding="utf-8") as f:
                custom_config = yaml.safe_load(f)
            if custom_config:
                from actions.builtin import _load_custom_actions
                _load_custom_actions(action_registry, custom_config)
        except Exception as e:
            log.warning(f"Custom actions load failed: {e}")

    actions = action_registry.list_actions()
    log.info(f"Loaded {len(actions)} actions:")
    for name, pri, _ in actions:
        log.info(f"  [{pri:3d}] {name}")


# ---- TTS ----
TTS_ENABLED = _config.get("tts", {}).get("enabled", True)


def speak(text: str):
    """Windows SAPI text-to-speech."""
    if not TTS_ENABLED:
        return
    safe = text.replace('"', "'").replace("\\", "\\\\")
    def _run():
        import subprocess
        subprocess.run(
            ["powershell", "-NoP", "-C",
             "Add-Type -As System.Speech;"
             f"(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{safe}')"],
            creationflags=0x08000000
        )
    threading.Thread(target=_run, daemon=True).start()


# ---- Main ----
_last_send = 0
_streamer = None  # Global streaming recognizer


def _dispatch_text(text: str):
    """Dispatch recognized text through the action pipeline."""
    global _last_send
    now = time.time()
    if now - _last_send < 1.0:
        return  # Debounce
    _last_send = now

    result = action_registry.dispatch(text)
    if result.handled:
        log.info(f"  → [{result.action_name}] {result.message}")
    return result


def _check_wake_word(text: str, prev_text: str) -> tuple:
    """
    Check if new text contains the wake word.
    Returns (has_wake, command_text, updated_prev_text).
    Uses deduplicated incremental approach to avoid re-triggering.
    """
    if WAKE_WORD in text:
        # Find where wake word appears and extract command after it
        idx = text.find(WAKE_WORD)
        cmd = text[idx + len(WAKE_WORD):].strip()
        return True, cmd
    return False, ""


def run_streaming():
    """
    🆕 Streaming mode: continuous sliding-window recognition.
    Real-time text appears in overlay as you speak.
    """
    global _last_send
    log.info(f"🎙️ Streaming mode active — {WAKE_WORD} detected in real-time")

    streamer = StreamingRecognizer(language=LANGUAGE)
    streamer.start()
    overlay("Stream", f"实时监听中 — 说'{WAKE_WORD}'唤醒")

    waiting_cmd = False
    cmd_buffer = np.array([], dtype=np.float32)
    cmd_deadline = 0
    last_overlay_text = ""

    def on_text(new_partial, full_text):
        nonlocal waiting_cmd, cmd_buffer, cmd_deadline, last_overlay_text

        display = full_text[-80:] if full_text else "语音待机中..."
        if display != last_overlay_text:
            overlay("Live" if full_text else "Idle", display)
            last_overlay_text = display

        if waiting_cmd:
            # Collecting command after wake word
            if time.time() < cmd_deadline and new_partial:
                log.info(f"[Stream] {new_partial}")
        else:
            # Check for wake word in latest text
            has_wake, cmd = _check_wake_word(full_text, "")
            if has_wake:
                if cmd:
                    # Wake word + command in same utterance
                    log.info(f"[Stream+Wake] {cmd}")
                    overlay("Action", cmd)
                    _dispatch_text(cmd)
                else:
                    # Wake word only — start command mode
                    overlay("Wake", "请说话...")
                    speak("我在听")
                    waiting_cmd = True
                    cmd_deadline = time.time() + PHRASE_LIMIT
                    cmd_buffer = np.array([], dtype=np.float32)
                    # Reset streamer to capture clean command
                    # We'll just use a fresh buffer by noting the current length
                    streamer._full_text = ""
                    streamer._prev_text = ""

    streamer.on_result = on_text

    try:
        chunk_samples = STREAM_RATE // 10  # 100ms frames
        while True:
            try:
                frame = source.stream.read(chunk_samples, exception_on_overflow=False)
            except IOError:
                continue

            audio_np = np.frombuffer(frame, dtype=np.int16).astype(np.float32) / 32768.0

            if waiting_cmd:
                cmd_buffer = np.concatenate([cmd_buffer, audio_np])
                if time.time() > cmd_deadline:
                    # Time's up — recognize the command chunk
                    if len(cmd_buffer) > STREAM_RATE * 0.3:
                        wav_bytes = core.asr._float32_to_wav_bytes(cmd_buffer, STREAM_RATE)
                        model = core.asr._small_model if DUAL_MODEL else core.asr._tiny_model
                        try:
                            segs, _ = model.transcribe(wav_bytes, language=LANGUAGE, beam_size=5)
                            cmd_text = "".join(s.text.strip() for s in segs)
                            if cmd_text:
                                log.info(f"[Stream+CMD] {cmd_text}")
                                overlay("Action", cmd_text)
                                _dispatch_text(cmd_text)
                        except:
                            pass
                    waiting_cmd = False
                    cmd_buffer = np.array([], dtype=np.float32)
                    overlay("Idle", "语音待机中...")

            streamer.feed(audio_np)

    except KeyboardInterrupt:
        pass
    finally:
        final = streamer.stop()
        if final:
            log.info(f"[Stream Final] {final}")
        log.info("Streaming stopped")


def run_legacy():
    """
    Legacy mode: listen → complete phrase → recognize → dispatch.
    Simpler, works better for slow CPUs or single-model setups.
    """
    global _last_send
    log.info("Legacy mode active (phrase-based)")

    overlay("Ready", f"v3 已就绪 — 说'{WAKE_WORD}'唤醒")
    waiting_cmd = False

    while True:
        try:
            with mic as s:
                audio = recognizer.listen(
                    s,
                    timeout=5 if waiting_cmd else None,
                    phrase_time_limit=PHRASE_LIMIT
                )

            use_small = waiting_cmd
            text = recognize(audio, use_small=use_small, language=LANGUAGE).strip()

            if not text:
                if not waiting_cmd:
                    overlay("Idle", "语音待机中...")
                continue

            log.info(f"[Heard] {text}")
            overlay("Heard", text)

            if waiting_cmd:
                overlay("Action", text)
                _dispatch_text(text)
                waiting_cmd = False
                continue

            if WAKE_WORD in text:
                cmd = text.split(WAKE_WORD, 1)[1].strip()
                if cmd:
                    overlay("Action", cmd)
                    _dispatch_text(cmd)
                else:
                    overlay("Wake", "请说话...")
                    speak("我在听")
                    waiting_cmd = True

        except sr.WaitTimeoutError:
            if waiting_cmd:
                overlay("Idle", "语音待机中...")
                waiting_cmd = False
        except KeyboardInterrupt:
            break
        except Exception as e:
            log.error(f"Loop error: {e}")
            time.sleep(0.3)


def main():
    log.info("=" * 55)
    log.info("  Voice Wake v3 'Jarvis' — Unlimited Voice Assistant")
    log.info(f"  Wake: '{WAKE_WORD}' | Streaming: {STREAMING} | Dual: {DUAL_MODEL}")
    log.info("  Actions: system → custom → shell → AI assistant")
    log.info("  Press Ctrl+C to exit")
    log.info("=" * 55)

    try:
        if STREAMING:
            run_streaming()
        else:
            run_legacy()
    except KeyboardInterrupt:
        log.info("Service stopped")
        overlay("Stop", "服务已停止")


if __name__ == "__main__":
    import core.asr  # For _float32_to_wav_bytes access in streaming dispatcher

    # ---- Initialization ----
    init_models()
    init_actions()

    # ---- Audio setup ----
    if STREAMING:
        # Streaming mode: use raw pyaudio stream directly
        import pyaudio
        pa = pyaudio.PyAudio()
        STREAM_RATE = 16000
        try:
            source = pa.open(
                format=pyaudio.paInt16, channels=1, rate=STREAM_RATE,
                input=True, frames_per_buffer=STREAM_RATE // 10
            )
            source.start_stream()
            log.info(f"Stream mic OK | rate={STREAM_RATE}")
        except Exception as e:
            log.error(f"Stream mic failed: {e}")
            sys.exit(1)

        recognizer = None
        mic = None
    else:
        # Legacy mode: use SpeechRecognition wrapper
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = ENERGY_THRESHOLD
        recognizer.dynamic_energy_threshold = DYNAMIC_ENERGY
        recognizer.pause_threshold = PAUSE_THRESHOLD
        recognizer.operation_timeout = None

        try:
            mic = sr.Microphone()
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
            if not DYNAMIC_ENERGY:
                recognizer.energy_threshold = max(recognizer.energy_threshold, ENERGY_THRESHOLD)
            log.info(f"Legacy mic OK | threshold={recognizer.energy_threshold} | pause={PAUSE_THRESHOLD}s")
        except Exception as e:
            log.error(f"Mic init failed: {e}")
            sys.exit(1)

    main()
