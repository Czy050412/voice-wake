# -*- coding: utf-8 -*-
"""
System Commands Action — voice-controlled Windows operations.
Port of voice_commands.py as a pluggable action.
"""
import os
import subprocess
import datetime
import ctypes
from ctypes import wintypes

from ..base import BaseAction, ActionResult

u32 = ctypes.windll.user32


class SystemCommandsAction(BaseAction):
    """Voice-controlled system operations: open apps, volume, lock, screenshot, time, power."""

    name = "system_commands"
    priority = 1  # Highest priority — system commands are fast and deterministic

    # App registry
    APPS = {
        "qq音乐": "F:\\QQMusic\\QQMusic.exe",
        "qq": ("C:\\Program Files\\Tencent\\QQNT\\QQ.exe",
               "C:\\Program Files (x86)\\Tencent\\QQNT\\QQ.exe"),
        "微信": ("C:\\Program Files\\Tencent\\WeChat\\WeChat.exe",
                 "C:\\Program Files (x86)\\Tencent\\WeChat\\WeChat.exe"),
        "浏览器": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "edge": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
        "计算器": "calc.exe", "记事本": "notepad.exe", "cmd": "cmd.exe",
        "任务管理器": "taskmgr.exe", "资源管理器": "explorer.exe",
        "控制面板": "control.exe", "画图": "mspaint.exe",
        "ue": ("F:\\UE_5.4\\Engine\\Binaries\\Win64\\UnrealEditor.exe",
               "C:\\Program Files\\Epic Games\\UE_5.4\\Engine\\Binaries\\Win64\\UnrealEditor.exe"),
    }

    WEBSITES = {
        "百度": "https://www.baidu.com", "谷歌": "https://www.google.com",
        "b站": "https://www.bilibili.com", "bilibili": "https://www.bilibili.com",
        "github": "https://github.com", "知乎": "https://www.zhihu.com",
        "淘宝": "https://www.taobao.com", "京东": "https://www.jd.com",
        "斗鱼": "https://www.douyu.com", "虎牙": "https://www.huya.com",
    }

    SYS_KEYWORDS = [
        "打开", "启动", "音量", "锁屏", "截图", "关机", "重启", "睡眠",
        "时间", "几点", "日期", "几号", "电量", "静音", "声音",
    ]

    def can_handle(self, text: str) -> bool:
        return any(kw in text for kw in self.SYS_KEYWORDS)

    def execute(self, text: str) -> ActionResult:
        text = text.strip()

        # Volume control
        if any(w in text for w in ["音量", "静音", "声音"]):
            ok = self._control_volume(text)
            return ActionResult(handled=True, action_name="音量", success=ok, message="音量控制")

        # Lock screen
        if "锁屏" in text or ("锁定" in text and "屏幕" not in text):
            u32.LockWorkStation()
            return ActionResult(handled=True, action_name="锁屏", success=True, message="屏幕已锁定")

        # Screenshot
        if any(w in text for w in ["截图", "截屏"]):
            ok = self._screenshot()
            return ActionResult(handled=True, action_name="截图", success=ok,
                                message="截图已保存" if ok else "截图失败")

        # Power
        if any(w in text for w in ["关机", "重启", "睡眠", "取消关机"]):
            ok = self._power(text)
            return ActionResult(handled=True, action_name="电源", success=ok, message="电源操作")

        # Time/date/battery
        if any(w in text for w in ["时间", "几点", "日期", "几号", "电量"]):
            msg = self._system_info(text)
            return ActionResult(handled=True, action_name="信息", success=True, message=msg)

        # Open app/website
        if any(w in text for w in ["打开", "启动", "运行"]):
            content = text.replace("打开", "").replace("启动", "").replace("运行", "").strip()

            # Try websites first
            for kw, url in self.WEBSITES.items():
                if kw in content:
                    subprocess.Popen(["cmd", "/c", "start", url], shell=True)
                    return ActionResult(handled=True, action_name="打开网站", success=True,
                                        message=f"已打开{kw}")

            # Try apps
            ok = self._launch_app(content)
            return ActionResult(handled=True, action_name="打开应用",
                                success=ok, message=f"已打开{content}" if ok else "未找到应用")

        return ActionResult(handled=False)

    # ---- Internal handlers ----

    def _launch_app(self, name: str) -> bool:
        name_l = name.lower().strip()
        path = self.APPS.get(name_l)
        if not path:
            for key, val in self.APPS.items():
                if key in name_l or name_l in key:
                    path = val
                    break
        if not path:
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
            return True
        except:
            return False

    def _control_volume(self, action: str) -> bool:
        VK_UP, VK_DOWN, VK_MUTE = 0xAF, 0xAE, 0xAD
        try:
            import win32api
            if any(w in action for w in ["大", "加", "up"]):
                for _ in range(5):
                    win32api.keybd_event(VK_UP, 0, 0, 0)
                    win32api.keybd_event(VK_UP, 0, 2, 0)
            elif any(w in action for w in ["小", "减", "down"]):
                for _ in range(5):
                    win32api.keybd_event(VK_DOWN, 0, 0, 0)
                    win32api.keybd_event(VK_DOWN, 0, 2, 0)
            elif "静音" in action or "mute" in action:
                win32api.keybd_event(VK_MUTE, 0, 0, 0)
                win32api.keybd_event(VK_MUTE, 0, 2, 0)
            return True
        except:
            return False

    def _screenshot(self) -> bool:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        fn = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(desktop, fn)
        try:
            subprocess.run([
                "powershell", "-c",
                "Add-Type -As System.Windows.Forms;"
                "$s=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;"
                "$b=New-Object System.Drawing.Bitmap($s.Width,$s.Height);"
                "$g=[System.Drawing.Graphics]::FromImage($b);"
                "$g.CopyFromScreen($s.X,$s.Y,0,0,$s.Size);"
                f"$b.Save('{path.replace(chr(92), chr(92)+chr(92))}');"
            ], capture_output=True, timeout=10)
            return True
        except:
            return False

    def _power(self, action: str) -> bool:
        if "关机" in action:
            subprocess.Popen("shutdown /s /t 10", shell=True)
        elif "重启" in action:
            subprocess.Popen("shutdown /r /t 10", shell=True)
        elif "睡眠" in action:
            subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
        elif "取消关机" in action:
            subprocess.Popen("shutdown /a", shell=True)
        return True

    def _system_info(self, req: str) -> str:
        now = datetime.datetime.now()
        if "时间" in req or "几点" in req:
            return f"现在是{now.hour}点{now.minute}分"
        if "日期" in req or "几号" in req:
            w = ["一","二","三","四","五","六","日"][now.weekday()]
            return f"今天是{now.year}年{now.month}月{now.day}日，星期{w}"
        if "电量" in req:
            try:
                r = subprocess.run(
                    ["powershell", "-c", "(Get-WmiObject Win32_Battery).EstimatedChargeRemaining"],
                    capture_output=True, text=True, timeout=5)
                pct = r.stdout.strip()
                if pct and pct.isdigit():
                    return f"电池剩余百分之{pct}"
            except:
                pass
        return "这个信息我还获取不到"
