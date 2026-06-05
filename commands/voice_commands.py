# -*- coding: utf-8 -*-
"""
Voice Commands Module - Voice-controlled Windows system actions.
Triggered by command keywords after the wake word.
"""
import os
import sys
import subprocess
import ctypes
import time
import threading
from ctypes import wintypes

# ======================== System API ========================
u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32


def speak(text):
    """Text-to-speech using Windows SAPI"""
    safe = text.replace('"', "'").replace("\\", "\\\\").replace("\n", " ")
    def _s():
        subprocess.run(
            ["powershell", "-NoP", "-C",
             "Add-Type -As System.Speech;"
             "(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{}')".format(safe)],
            creationflags=0x08000000
        )
    threading.Thread(target=_s, daemon=True).start()


def log(msg):
    try:
        log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "voice_wake.log")
        line = "[{}] {}".format(time.strftime("%H:%M:%S"), msg)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass


# ======================== Command Handlers ========================

def launch_app(app_name):
    """Launch an application by name"""
    apps = {
        "qq音乐": "F:\\QQMusic\\QQMusic.exe",
        "qq": ("C:\\Program Files\\Tencent\\QQNT\\QQ.exe",
               "C:\\Program Files (x86)\\Tencent\\QQNT\\QQ.exe"),
        "微信": ("C:\\Program Files\\Tencent\\WeChat\\WeChat.exe",
                 "C:\\Program Files (x86)\\Tencent\\WeChat\\WeChat.exe"),
        "浏览器": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "edge": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
        "计算器": "calc.exe",
        "记事本": "notepad.exe",
        "cmd": "cmd.exe",
        "任务管理器": "taskmgr.exe",
        "资源管理器": "explorer.exe",
        "控制面板": "control.exe",
        "截图工具": "SnippingTool.exe",
        "画图": "mspaint.exe",
    }

    app_name_lower = app_name.lower().strip()
    path = apps.get(app_name_lower)

    if not path:
        # Try partial match
        for key, val in apps.items():
            if key in app_name_lower or app_name_lower in key:
                path = val
                break

    if not path:
        speak("没找到{}，请手动打开".format(app_name))
        return False

    if isinstance(path, tuple):
        for p in path:
            if os.path.exists(p):
                path = p
                break
        else:
            path = path[0]

    try:
        subprocess.Popen(path, shell=True)
        speak("已打开{}".format(app_name))
        return True
    except Exception as e:
        speak("打开{}失败".format(app_name))
        return False


def control_volume(action):
    """Control system volume"""
    import win32api
    try:
        VK_VOLUME_UP = 0xAF
        VK_VOLUME_DOWN = 0xAE
        VK_VOLUME_MUTE = 0xAD

        if "大" in action or "加" in action or "up" in action.lower():
            for _ in range(5):
                win32api.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                win32api.keybd_event(VK_VOLUME_UP, 0, 2, 0)
            speak("音量已加大")
        elif "小" in action or "减" in action or "down" in action.lower():
            for _ in range(5):
                win32api.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
                win32api.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
            speak("音量已减小")
        elif "静音" in action or "mute" in action.lower():
            win32api.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
            win32api.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
            speak("已切换静音")
        return True
    except:
        # Fallback: use PowerShell
        try:
            if "大" in action or "加" in action:
                for _ in range(5):
                    subprocess.run(["powershell", "-c", "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"], capture_output=True)
                speak("音量已加大")
            elif "小" in action or "减" in action:
                for _ in range(5):
                    subprocess.run(["powershell", "-c", "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"], capture_output=True)
                speak("音量已减小")
        except:
            speak("音量控制失败")
            return False
    return True


def lock_screen():
    """Lock the workstation"""
    u32.LockWorkStation()
    speak("屏幕已锁定")


def screenshot():
    """Take a screenshot and save to desktop"""
    import datetime
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    filename = "screenshot_{}.png".format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    path = os.path.join(desktop, filename)
    try:
        subprocess.run([
            "powershell", "-c",
            "Add-Type -As System.Windows.Forms;"
            "$s=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;"
            "$b=New-Object System.Drawing.Bitmap($s.Width,$s.Height);"
            "$g=[System.Drawing.Graphics]::FromImage($b);"
            "$g.CopyFromScreen($s.X,$s.Y,0,0,$s.Size);"
            "$b.Save('{}');".format(path.replace("\\", "\\\\"))
        ], capture_output=True, timeout=10)
        speak("截图已保存")
        return True
    except:
        speak("截图失败")
        return False


def system_info(request_type):
    """Get system info and speak it"""
    import datetime

    if "时间" in request_type or "几点" in request_type:
        now = datetime.datetime.now()
        speak("现在是{}点{}分".format(now.hour, now.minute))
        return True

    if "日期" in request_type or "几号" in request_type:
        now = datetime.datetime.now()
        speak("今天是{}年{}月{}日，星期{}".format(
            now.year, now.month, now.day,
            ["一","二","三","四","五","六","日"][now.weekday()]
        ))
        return True

    # Try battery info
    if "电量" in request_type or "电池" in request_type:
        try:
            result = subprocess.run(
                ["powershell", "-c",
                 "(Get-WmiObject Win32_Battery).EstimatedChargeRemaining"],
                capture_output=True, text=True, timeout=5
            )
            pct = result.stdout.strip()
            if pct and pct.isdigit():
                speak("电池剩余百分之{}".format(pct))
                return True
        except:
            pass
        speak("无法获取电池信息")
        return False

    speak("这个信息我还获取不到")
    return False


def power_control(action):
    """Shutdown, restart, sleep"""
    actions = {
        "关机": ("shutdown /s /t 10", "电脑将在10秒后关机"),
        "重启": ("shutdown /r /t 10", "电脑将在10秒后重启"),
        "睡眠": ("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", ""),
        "取消关机": ("shutdown /a", "已取消关机"),
    }
    for key, (cmd, msg) in actions.items():
        if key in action:
            subprocess.Popen(cmd, shell=True)
            if msg:
                speak(msg)
            return True
    return False


def open_website(site):
    """Open website in default browser"""
    sites = {
        "百度": "https://www.baidu.com",
        "谷歌": "https://www.google.com",
        "b站": "https://www.bilibili.com",
        "bilibili": "https://www.bilibili.com",
        "github": "https://github.com",
        "知乎": "https://www.zhihu.com",
        "淘宝": "https://www.taobao.com",
        "京东": "https://www.jd.com",
        "斗鱼": "https://www.douyu.com",
        "虎牙": "https://www.huya.com",
    }
    url = sites.get(site.lower())
    if not url:
        # Try matching
        for key, val in sites.items():
            if key in site.lower():
                url = val
                break
    if url:
        subprocess.Popen(["cmd", "/c", "start", url], shell=True)
        speak("已打开{}".format(site))
        return True
    speak("没找到网站{}".format(site))
    return False


# ======================== Command Router ========================

COMMANDS = {
    # Pattern: (keywords, handler_function, description)
    "打开": (
        lambda text: any(kw in text for kw in ["打开", "启动", "运行"]),
        lambda text: _handle_open(text),
        "打开/启动应用或网站"
    ),
    "音量": (
        lambda text: "音量" in text or "静音" in text or "声音" in text,
        lambda text: control_volume(text),
        "控制音量大小/静音"
    ),
    "锁屏": (
        lambda text: "锁屏" in text or "锁定" in text,
        lambda text: lock_screen(),
        "锁定电脑屏幕"
    ),
    "截图": (
        lambda text: "截图" in text or "截屏" in text or "屏幕截图" in text,
        lambda text: screenshot(),
        "截取当前屏幕"
    ),
    "关机": (
        lambda text: any(kw in text for kw in ["关机", "重启", "睡眠", "取消关机"]),
        lambda text: power_control(text),
        "电源控制（关机/重启/睡眠）"
    ),
    "时间": (
        lambda text: any(kw in text for kw in ["时间", "几点", "日期", "几号", "电量"]),
        lambda text: system_info(text),
        "查询系统时间/日期/电量"
    ),
}


def _handle_open(text):
    """Route 'open' commands to app or website"""
    # Remove command prefixes
    text = text.replace("打开", "").replace("启动", "").replace("运行", "").strip()

    # Try known websites first
    website_keywords = ["百度", "谷歌", "b站", "bilibili", "github", "知乎", "淘宝", "京东", "斗鱼", "虎牙"]
    for kw in website_keywords:
        if kw in text:
            return open_website(text)

    # Try apps
    return launch_app(text)


def execute_command(text):
    """Parse text and execute matching command"""
    text = text.strip()
    if not text:
        return None

    for name, (check, handler, desc) in COMMANDS.items():
        try:
            if check(text):
                log("[CMD] {} -> {}".format(name, text[:50]))
                result = handler(text)
                return (name, result, desc)
        except Exception as e:
            log("  Command '{}' error: {}".format(name, e))

    return None


if __name__ == "__main__":
    # Quick test
    print("Starting voice command test...")
    speak("语音命令模块已就绪")
    print("Available commands:")
    for name, (_, _, desc) in COMMANDS.items():
        print("  {} - {}".format(name, desc))
