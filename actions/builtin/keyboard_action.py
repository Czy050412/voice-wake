# -*- coding: utf-8 -*-
"""Keyboard macro action — send keystroke sequences."""
import pyautogui
from ..base import BaseAction, ActionResult


class KeyboardAction(BaseAction):
    """Send keyboard macros — useful for hotkey-driven tools, games, etc."""

    name = "keyboard"
    priority = 20
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.05

    def __init__(self, name="keyboard", priority=20, macro="", trigger_keywords=None):
        self.name = name
        self.priority = priority
        self._macro = macro  # Format: "ctrl+s" or "alt+tab" or "win+d"
        self._keywords = trigger_keywords or []

    def can_handle(self, text: str) -> bool:
        if not self._macro or not self._keywords:
            return False
        return any(kw in text for kw in self._keywords)

    def execute(self, text: str) -> ActionResult:
        try:
            parts = self._macro.lower().split("+")
            if len(parts) > 1:
                pyautogui.hotkey(*parts)
            else:
                pyautogui.press(self._macro)
            return ActionResult(handled=True, action_name=self.name, success=True,
                                message=f"已发送: {self._macro}")
        except Exception as e:
            return ActionResult(handled=True, action_name=self.name, success=False,
                                message=str(e))
