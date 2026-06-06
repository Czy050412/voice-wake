# -*- coding: utf-8 -*-
"""
AI Assistant Action — generic integration with any AI IDE/chat tool.
Replaces the hardcoded WorkBuddy integration. Auto-detects or configurable.
"""
import os
import re
import ctypes
import ctypes.wintypes as wintypes
import subprocess
import threading
import time

import pyautogui
import pyperclip

from ..base import BaseAction, ActionResult

# Win32 types
u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32

class RECT(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                ("right", wintypes.LONG), ("bottom", wintypes.LONG)]


class AIAssistantAction(BaseAction):
    """Send recognized text to any AI assistant window — auto-detect or configure."""

    name = "ai_assistant"
    priority = 100  # Last resort — try system commands first

    # Default target: any of these windows
    TARGETS = [
        # Process name matches
        {"process": "WorkBuddy.exe", "title_match": None},
        {"process": "CodeBuddy.exe", "title_match": None},
        {"process": "Cursor.exe", "title_match": None},
        {"process": "Windsurf.exe", "title_match": None},
        {"process": "Trae.exe", "title_match": None},
        # Title keyword matches
        {"process": None, "title_match": "WorkBuddy"},
        {"process": None, "title_match": "CodeBuddy"},
        {"process": None, "title_match": "ChatGPT"},
        {"process": None, "title_match": "deepseek", "url": "https://chat.deepseek.com"},
        {"process": None, "title_match": "Kimi", "url": "https://kimi.moonshot.cn"},
        {"process": None, "title_match": "通义千问", "url": "https://tongyi.aliyun.com"},
    ]

    def __init__(self, config: dict = None):
        self._config = config or {}
        self._last_send = 0
        self._cooldown = float(self._config.get("cooldown", 3.0))
        self._input_offset_y = int(self._config.get("input_offset_y", -180))
        self._pos_cfg = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "input_pos.cfg"
        )
        self._calibrated = self._load_calibration()

    def _load_calibration(self):
        try:
            if os.path.exists(self._pos_cfg):
                with open(self._pos_cfg, "r", encoding="utf-8") as f:
                    parts = f.read().strip().split()
                if len(parts) >= 2:
                    return (int(parts[0]), int(parts[1]))
        except:
            pass
        return None

    def can_handle(self, text: str) -> bool:
        # This is the catch-all — handles everything not caught by system commands
        return True

    def execute(self, text: str) -> ActionResult:
        now = time.time()
        if now - self._last_send < self._cooldown:
            return ActionResult(handled=True, action_name="AI", success=False,
                                message="冷却中，请稍候")

        self._last_send = now
        hwnd = self._find_target()
        if hwnd:
            threading.Thread(target=self._type_and_send, args=(text, hwnd), daemon=True).start()
            return ActionResult(handled=True, action_name="AI", success=True,
                                message=f"已发送到AI助手")
        else:
            # No window found — just copy to clipboard
            pyperclip.copy(text)
            return ActionResult(handled=True, action_name="AI", success=True,
                                message="文本已复制到剪贴板（未找到AI窗口）")

    def _find_target(self):
        """Try to find any configured AI assistant window."""
        targets = self._config.get("targets", self.TARGETS)

        for t in targets:
            # Try process name
            if t.get("process"):
                hwnd = self._find_by_process(t["process"])
                if hwnd:
                    return hwnd
            # Try title keyword
            if t.get("title_match"):
                hwnd = self._find_by_title(t["title_match"])
                if hwnd:
                    return hwnd

        return None

    def _find_by_process(self, name: str):
        result = [None]
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, ctypes.c_int)

        def cb(hwnd, _):
            if result[0]:
                return False
            if not u32.IsWindowVisible(hwnd):
                return True
            pid = wintypes.DWORD()
            u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            h = k32.OpenProcess(0x0400, False, pid)
            if not h:
                return True
            try:
                buf = ctypes.create_unicode_buffer(512)
                size = wintypes.DWORD(512)
                if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                    if os.path.basename(buf.value).lower() == name.lower():
                        result[0] = hwnd
                        return False
            finally:
                k32.CloseHandle(h)
            return True

        u32.EnumWindows(WNDENUMPROC(cb), 0)
        return result[0]

    def _find_by_title(self, keyword: str):
        result = [None]
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, ctypes.c_int)

        def cb(hwnd, _):
            if result[0]:
                return False
            if not u32.IsWindowVisible(hwnd):
                return True
            buf = ctypes.create_unicode_buffer(512)
            u32.GetWindowTextW(hwnd, buf, 512)
            if keyword.lower() in buf.value.lower():
                result[0] = hwnd
                return False
            return True

        u32.EnumWindows(WNDENUMPROC(cb), 0)
        return result[0]

    def _bring_to_front(self, hwnd):
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

    def _get_input_pos(self, hwnd):
        if self._calibrated:
            return self._calibrated
        rect = RECT()
        if u32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return ((rect.left + rect.right) // 2, rect.bottom + self._input_offset_y)
        return None

    def _type_and_send(self, message, hwnd):
        try:
            self._bring_to_front(hwnd)
            time.sleep(0.6)
            pos = self._get_input_pos(hwnd)
            if pos:
                pyautogui.click(pos[0], pos[1], duration=0.15)
            time.sleep(0.2)
            pyperclip.copy(message)
            time.sleep(0.15)
            pyautogui.hotkey("ctrl", "v", interval=0.03)
            time.sleep(0.2)
            pyautogui.press("enter")
        except Exception:
            pyperclip.copy(message)  # Fallback
