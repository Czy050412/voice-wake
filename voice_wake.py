# -*- coding: utf-8 -*-
"""
Voice Wake - Modular Offline Voice Assistant for Windows
  Core engine: faster-whisper (local) + Win32 automation
  Plugins: system commands, WorkBuddy integration, TTS feedback
"""
import ctypes
import ctypes.wintypes as wintypes
import os
import sys
import tempfile
import threading
import time

import pyautogui
import pyperclip
import speech_recognition as sr

# ======================== Paths ========================
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(APP_DIR, "core")
CFG_DIR = os.path.join(APP_DIR, "config")
CMD_DIR = os.path.join(APP_DIR, "commands")

sys.path.insert(0, APP_DIR)
sys.path.insert(0, CMD_DIR)

# ======================== Config ========================
WAKE_WORD = "狗蛋"
LANGUAGE = "zh"
MODEL_SIZE = "small"
ENERGY_THRESHOLD = 300
PAUSE_THRESHOLD = 1.5
PHRASE_LIMIT = 15
SEND_COOLDOWN = 5.0
INPUT_OFFSET_Y = -180
TTS_ENABLED = True
CMDS_ENABLED = True
BUDDY_ENABLED = True

try:
    import yaml
    cfg_path = os.path.join(CFG_DIR, "settings.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        if cfg:
            WAKE_WORD = cfg.get("wake_word", WAKE_WORD)
            LANGUAGE = cfg.get("language", LANGUAGE)
            MODEL_SIZE = cfg.get("model", MODEL_SIZE)
            TTS_ENABLED = cfg.get("tts", {}).get("enabled", TTS_ENABLED)
            CMDS_ENABLED = cfg.get("commands", {}).get("enabled", CMDS_ENABLED)
            BUDDY_ENABLED = cfg.get("workbuddy", {}).get("enabled", BUDDY_ENABLED)
            INPUT_OFFSET_Y = cfg.get("workbuddy", {}).get("input_offset_y", INPUT_OFFSET_Y)
            adv = cfg.get("advanced", {})
            ENERGY_THRESHOLD = adv.get("energy_threshold", ENERGY_THRESHOLD)
            PAUSE_THRESHOLD = adv.get("pause_threshold", PAUSE_THRESHOLD)
            PHRASE_LIMIT = adv.get("phrase_limit", PHRASE_LIMIT)
            SEND_COOLDOWN = adv.get("send_cooldown", SEND_COOLDOWN)
except Exception:
    pass

TTS_FILE = os.path.join(APP_DIR, "tts.txt")
CMD_FILE = os.path.join(APP_DIR, "voice_cmd.txt")
LOG_FILE = os.path.join(APP_DIR, "voice_wake.log")
POS_CFG = os.path.join(APP_DIR, "input_pos.cfg")
WHISPER_CACHE = os.path.join(APP_DIR, ".whisper_cache")

# Disable pyautogui fail-safe
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.1

# ======================== Logging ========================
def log(msg):
    line = "[{}] {}".format(time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ======================== ASR Engine ========================
asr_model = None

def init_asr():
    global asr_model
    log("Loading faster-whisper model: {} ...".format(MODEL_SIZE))
    try:
        from faster_whisper import WhisperModel
        asr_model = WhisperModel(
            MODEL_SIZE,
            device="cpu",
            compute_type="int8",
            download_root=WHISPER_CACHE,
        )
        log("ASR engine ready (offline)")
    except Exception as e:
        log("ASR init ERROR: {}".format(e))
        asr_model = None


def recognize(audio_data):
    if asr_model is None:
        try:
            return r.recognize_google(audio_data, language="zh-CN")
        except:
            return ""
    wav_data = audio_data.get_wav_data()
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".wav", dir=APP_DIR)
        os.close(fd)
        with open(tmp_path, "wb") as f:
            f.write(wav_data)
        segments, _ = asr_model.transcribe(
            tmp_path, language=LANGUAGE, beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        texts = [s.text.strip() for s in segments]
        return "".join(texts)
    except Exception as e:
        log("  ASR error: {}".format(e))
        return ""
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try: os.unlink(tmp_path)
            except: pass


# ======================== System Commands ========================
_cmd_executor = None

def init_commands():
    global _cmd_executor
    if not CMDS_ENABLED:
        return
    try:
        from voice_commands import execute_command as ec
        _cmd_executor = ec
        log("System commands module loaded")
    except Exception as e:
        log("Commands module load error: {}".format(e))


def try_system_command(text):
    """Route text to system commands if it doesn't look like a WorkBuddy query"""
    if _cmd_executor is None:
        return False
    # Heuristic: if text contains system action keywords, try commands first
    sys_keywords = ["打开", "启动", "音量", "锁屏", "截图", "关机", "重启", "时间", "几点", "电量"]
    if any(kw in text for kw in sys_keywords):
        result = _cmd_executor(text)
        if result:
            name, ok, desc = result
            log("[CMD] {} executed: {}".format(name, ok))
            return True
    return False


# ======================== Win32 Window Management ========================
u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32

class RECT(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                ("right", wintypes.LONG), ("bottom", wintypes.LONG)]

u32.IsWindowVisible.argtypes = [wintypes.HWND]
u32.IsWindowVisible.restype = wintypes.BOOL
u32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
u32.GetWindowTextW.restype = ctypes.c_int
u32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
u32.GetWindowRect.restype = wintypes.BOOL
u32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
u32.ShowWindow.restype = wintypes.BOOL
u32.SetForegroundWindow.argtypes = [wintypes.HWND]
u32.SetForegroundWindow.restype = wintypes.BOOL
u32.BringWindowToTop.argtypes = [wintypes.HWND]
u32.BringWindowToTop.restype = wintypes.BOOL
u32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
u32.GetWindowThreadProcessId.restype = wintypes.DWORD
u32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
u32.AttachThreadInput.restype = wintypes.BOOL
k32.GetCurrentThreadId.restype = wintypes.DWORD
k32.GetConsoleWindow.restype = wintypes.HWND
k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
k32.OpenProcess.restype = wintypes.HANDLE
k32.CloseHandle.argtypes = [wintypes.HANDLE]
k32.CloseHandle.restype = wintypes.BOOL
k32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
k32.QueryFullProcessImageNameW.restype = wintypes.BOOL


def find_window_by_process(process_name):
    _ENUM = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, ctypes.c_int)
    result = [None]
    def _cb(hwnd, _):
        if result[0]: return False
        if not u32.IsWindowVisible(hwnd): return True
        pid = wintypes.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        hProcess = k32.OpenProcess(0x0400, False, pid)
        if not hProcess: return True
        try:
            buf = ctypes.create_unicode_buffer(512)
            size = wintypes.DWORD(512)
            if k32.QueryFullProcessImageNameW(hProcess, 0, buf, ctypes.byref(size)):
                if os.path.basename(buf.value).lower() == process_name.lower():
                    result[0] = hwnd
                    return False
        finally:
            k32.CloseHandle(hProcess)
        return True
    u32.EnumWindows(_ENUM(_cb), 0)
    return result[0]


def find_window_by_title(keyword):
    _ENUM = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, ctypes.c_int)
    result = [None]
    def _cb(hwnd, _):
        if result[0]: return False
        if not u32.IsWindowVisible(hwnd): return True
        buf = ctypes.create_unicode_buffer(512)
        u32.GetWindowTextW(hwnd, buf, 512)
        if keyword.lower() in buf.value.lower():
            result[0] = hwnd
            return False
        return True
    u32.EnumWindows(_ENUM(_cb), 0)
    return result[0]


def find_workbuddy():
    hwnd = find_window_by_process("WorkBuddy.exe")
    if hwnd: return hwnd
    hwnd = find_window_by_title("WorkBuddy")
    if hwnd: return hwnd
    return find_window_by_title("CodeBuddy")


def bring_to_front(hwnd):
    my_tid = k32.GetCurrentThreadId()
    their_tid = u32.GetWindowThreadProcessId(hwnd, None)
    attached = False
    if my_tid != their_tid:
        attached = u32.AttachThreadInput(my_tid, their_tid, True)
    u32.ShowWindow(hwnd, 9)
    u32.BringWindowToTop(hwnd)
    u32.SetForegroundWindow(hwnd)
    if attached:
        u32.AttachThreadInput(my_tid, their_tid, False)


def load_calibrated_pos():
    try:
        if os.path.exists(POS_CFG):
            with open(POS_CFG, "r", encoding="utf-8") as f:
                parts = f.read().strip().split()
            if len(parts) >= 2:
                return (int(parts[0]), int(parts[1]))
    except:
        pass
    return None


CALIBRATED_POS = load_calibrated_pos()


def get_input_box_pos(hwnd):
    if CALIBRATED_POS:
        return CALIBRATED_POS
    rect = RECT()
    if not u32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    return ((rect.left + rect.right) // 2, rect.bottom + INPUT_OFFSET_Y)


def type_and_send(message, hwnd):
    try:
        console = k32.GetConsoleWindow()
        if console:
            u32.ShowWindow(console, 6)
        bring_to_front(hwnd)
        time.sleep(0.8)
        pos = get_input_box_pos(hwnd)
        if pos:
            pyautogui.click(pos[0], pos[1], duration=0.2)
        time.sleep(0.3)
        pyperclip.copy(message)
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "v", interval=0.05)
        time.sleep(0.3)
        pyautogui.press("enter")
        log("    -> Sent!")
    except Exception as e:
        log("    -> type_and_send error: {}".format(e))


# ======================== TTS ========================
def speak(text):
    safe = text.replace('"', "'").replace("\\", "\\\\").replace("\n", " ")
    def _s():
        import subprocess
        subprocess.run(
            ["powershell", "-NoP", "-C",
             "Add-Type -As System.Speech;"
             "(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{}')".format(safe)],
            creationflags=0x08000000
        )
    threading.Thread(target=_s, daemon=True).start()


last_tts_mtime = 0
def tts_loop():
    global last_tts_mtime
    if not TTS_ENABLED:
        return
    while True:
        time.sleep(0.5)
        if not os.path.exists(TTS_FILE): continue
        try:
            mt = os.path.getmtime(TTS_FILE)
            if mt > last_tts_mtime:
                last_tts_mtime = mt
                with open(TTS_FILE, "r", encoding="utf-8") as f:
                    msg = f.read().strip()
                if msg:
                    log("[TTS] {}".format(msg[:80]))
                    speak(msg)
        except: pass


# ======================== Send to WorkBuddy ========================
_last_send_time = 0

def send_to_buddy(message):
    global _last_send_time
    if not BUDDY_ENABLED:
        return
    now = time.time()
    if now - _last_send_time < SEND_COOLDOWN:
        log("    -> Cooldown, ignored")
        return
    _last_send_time = now

    log(">>> Sending: {}".format(message))
    with open(CMD_FILE, "a", encoding="utf-8") as f:
        f.write("[{}] {}\n".format(time.strftime("%H:%M:%S"), message))

    hwnd = find_workbuddy()
    if hwnd:
        log("    -> Found WorkBuddy, typing...")
        threading.Thread(target=type_and_send, args=(message, hwnd), daemon=True).start()
    else:
        log("    -> WorkBuddy not found, text in clipboard")
        pyperclip.copy(message)


# ======================== Main Loop ========================
def main():
    log("=" * 50)
    log("  Voice Wake v2.0 - Modular Voice Assistant")
    log("  Wake: \"{}\" | Engine: faster-whisper | Offline".format(WAKE_WORD))
    log("  Buddy:{}, Cmds:{}, TTS:{}".format(BUDDY_ENABLED, CMDS_ENABLED, TTS_ENABLED))
    log("  Press Ctrl+C to exit")
    log("=" * 50)

    waiting_cmd = False

    while True:
        try:
            with m as s:
                audio = r.listen(s, timeout=5 if waiting_cmd else None, phrase_time_limit=PHRASE_LIMIT)

            text = recognize(audio).strip()
            if not text:
                continue

            log("[Heard] {}".format(text))

            # Route to system command OR WorkBuddy based on content
            if CMDS_ENABLED and try_system_command(text):
                continue

            # WorkBuddy routing
            if not waiting_cmd:
                if WAKE_WORD in text:
                    cmd = text.split(WAKE_WORD, 1)[1].strip()
                    if cmd:
                        send_to_buddy(cmd)
                    else:
                        log("[Wake] Say your command...")
                        speaking = True if TTS_ENABLED else False
                        if TTS_ENABLED:
                            speak("我在听")
                        waiting_cmd = True
            else:
                send_to_buddy(text)
                waiting_cmd = False

        except sr.WaitTimeoutError:
            if waiting_cmd:
                log("[Timeout] Back to listening")
                waiting_cmd = False
        except KeyboardInterrupt:
            log("Service stopped")
            break
        except Exception as e:
            log("[Error] {}".format(e))
            time.sleep(0.5)


if __name__ == "__main__":
    # Init order matters
    init_asr()
    init_commands()

    # Audio capture
    r = sr.Recognizer()
    r.energy_threshold = ENERGY_THRESHOLD
    r.dynamic_energy_threshold = True
    r.pause_threshold = PAUSE_THRESHOLD
    r.operation_timeout = None
    try:
        m = sr.Microphone()
        with m as s:
            r.adjust_for_ambient_noise(s, duration=0.5)
        log("Microphone OK")
    except Exception as e:
        log("Mic ERROR: {}".format(e))
        sys.exit(1)

    # TTS loop
    threading.Thread(target=tts_loop, daemon=True).start()

    main()
