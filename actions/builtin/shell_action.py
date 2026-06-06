# -*- coding: utf-8 -*-
"""Shell command action — run arbitrary system commands."""
import subprocess
from ..base import BaseAction, ActionResult


class ShellAction(BaseAction):
    """Execute arbitrary shell commands. Configured via YAML."""

    name = "shell"
    priority = 50

    def __init__(self, name="shell", priority=50, command="", trigger_keywords=None):
        self.name = name
        self.priority = priority
        self._command = command
        self._keywords = trigger_keywords or []

    def can_handle(self, text: str) -> bool:
        if not self._keywords:
            return False
        return any(kw in text for kw in self._keywords)

    def execute(self, text: str) -> ActionResult:
        if not self._command:
            return ActionResult(handled=False)

        try:
            result = subprocess.run(
                self._command, shell=True,
                capture_output=True, text=True, timeout=30
            )
            return ActionResult(
                handled=True, action_name=self.name,
                success=(result.returncode == 0),
                message=result.stdout.strip()[:200] or "命令已执行"
            )
        except subprocess.TimeoutExpired:
            return ActionResult(handled=True, action_name=self.name, success=False,
                                message="命令执行超时")
        except Exception as e:
            return ActionResult(handled=True, action_name=self.name, success=False,
                                message=str(e))
