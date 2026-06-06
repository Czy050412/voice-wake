# -*- coding: utf-8 -*-
"""Python action — run custom Python scripts with access to recognized text."""
import os
import sys
import subprocess
from ..base import BaseAction, ActionResult

APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PythonAction(BaseAction):
    """Execute custom Python scripts. Script receives text via sys.argv[1]."""

    name = "python"
    priority = 20

    def __init__(self, name="python", priority=20, script="", trigger_keywords=None):
        self.name = name
        self.priority = priority
        self._script = script
        self._keywords = trigger_keywords or []

    def can_handle(self, text: str) -> bool:
        if not self._script or not self._keywords:
            return False
        return any(kw in text for kw in self._keywords)

    def execute(self, text: str) -> ActionResult:
        script_path = self._script
        if not os.path.isabs(script_path):
            script_path = os.path.join(APP_DIR, script_path)

        if not os.path.exists(script_path):
            return ActionResult(handled=True, action_name=self.name, success=False,
                                message=f"脚本不存在: {script_path}")

        try:
            venv_python = os.path.join(APP_DIR, ".venv", "Scripts", "python.exe")
            python_exe = venv_python if os.path.exists(venv_python) else sys.executable
            result = subprocess.run(
                [python_exe, script_path, text],
                capture_output=True, text=True, timeout=30,
                cwd=APP_DIR
            )
            return ActionResult(
                handled=True, action_name=self.name,
                success=(result.returncode == 0),
                message=result.stdout.strip()[:200] or "脚本已执行"
            )
        except subprocess.TimeoutExpired:
            return ActionResult(handled=True, action_name=self.name, success=False,
                                message="脚本执行超时")
        except Exception as e:
            return ActionResult(handled=True, action_name=self.name, success=False,
                                message=str(e))
