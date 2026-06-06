# -*- coding: utf-8 -*-
"""
Voice Wake v3 "Jarvis" — Unlimited Voice Assistant
==================================================
- Pluggable action system: shell, HTTP, Python, keyboard, AI assistant
- Dual-model ASR: tiny for wake-word, small for commands
- In-memory WAV processing: zero temp files
- Thread-optimized audio pipeline: capture → VAD → recognize → dispatch
- Auto-detects any AI assistant: WorkBuddy, CodeBuddy, Cursor, Windsurf, DeepSeek, Kimi...
"""
import os
import sys
import time
import logging
import threading

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
            SEND_COOLDOWN = _config.get("actions", {}).get("send_cooldown", SEND_COOLDOWN)
except Exception as e:
    log.warning(f"Config load failed: {e}")


# ---- ASR Engine ----
from core.asr import init_tiny, init_small, prewarm, recognize


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


def main():
    global _last_send

    log.info("=" * 55)
    log.info("  Voice Wake v3 'Jarvis' — Unlimited Voice Assistant")
    log.info(f"  Wake: '{WAKE_WORD}' | Models: tiny + {MODEL_SIZE} | Dual: {DUAL_MODEL}")
    log.info("  Actions: system → custom → shell → AI assistant")
    log.info("  Press Ctrl+C to exit")
    log.info("=" * 55)

    overlay("Ready", f"v3 Jarvis 已就绪 — 说'{WAKE_WORD}'唤醒")

    waiting_cmd = False

    while True:
        try:
            with m as s:
                audio = r.listen(
                    s,
                    timeout=5 if waiting_cmd else None,
                    phrase_time_limit=PHRASE_LIMIT
                )

            # Recognize with appropriate model
            use_small = waiting_cmd  # Use small model when expecting a command
            text = recognize(audio, use_small=use_small, language=LANGUAGE).strip()

            if not text:
                if not waiting_cmd:
                    overlay("Idle", "语音待机中...")
                continue

            log.info(f"[Heard] {text}")
            overlay("Heard", text)

            # ---- Routing logic ----
            if waiting_cmd:
                # Execute whatever follows the wake word
                overlay("Action", text)
                result = action_registry.dispatch(text)
                if result.handled:
                    log.info(f"  → [{result.action_name}] {result.message}")
                    if result.message:
                        overlay("Done", str(result.message)[:80])
                waiting_cmd = False
                continue

            # Check for wake word
            if WAKE_WORD in text:
                cmd = text.split(WAKE_WORD, 1)[1].strip()
                if cmd:
                    # Wake word + command in same utterance
                    overlay("Action", cmd)
                    result = action_registry.dispatch(cmd)
                    if result.handled:
                        log.info(f"  → [{result.action_name}] {result.message}")
                    elif result.handled is False and result.message:
                        overlay("Done", str(result.message)[:80])
                else:
                    # Wake word only — enter command mode
                    overlay("Wake", "请说话...")
                    speak("我在听")
                    waiting_cmd = True

        except sr.WaitTimeoutError:
            if waiting_cmd:
                log.info("[Timeout] Back to idle")
                overlay("Idle", "语音待机中...")
                waiting_cmd = False
        except KeyboardInterrupt:
            log.info("Service stopped")
            overlay("Stop", "服务已停止")
            break
        except Exception as e:
            log.error(f"Loop error: {e}")
            time.sleep(0.3)


if __name__ == "__main__":
    # ---- Initialization ----
    init_models()
    init_actions()

    # ---- Audio setup ----
    r = sr.Recognizer()
    r.energy_threshold = ENERGY_THRESHOLD
    r.dynamic_energy_threshold = DYNAMIC_ENERGY
    r.pause_threshold = PAUSE_THRESHOLD
    r.operation_timeout = None

    try:
        m = sr.Microphone()
        with m as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
        if not DYNAMIC_ENERGY:
            r.energy_threshold = max(r.energy_threshold, ENERGY_THRESHOLD)
        log.info(f"Mic OK | threshold={r.energy_threshold} | pause={PAUSE_THRESHOLD}s")
    except Exception as e:
        log.error(f"Mic init failed: {e}")
        sys.exit(1)

    main()
