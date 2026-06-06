# -*- coding: utf-8 -*-
"""
Built-in actions for Voice Wake v3.
System commands, AI assistant, shell, HTTP, Python, keyboard macros.
"""
from .system_commands import SystemCommandsAction
from .ai_assistant import AIAssistantAction
from .shell_action import ShellAction
from .http_action import HttpAction
from .python_action import PythonAction
from .keyboard_action import KeyboardAction


def load_builtins(registry, config: dict = None):
    """Register all built-in actions. User YAML actions inserted between system and AI."""
    from .registry import ActionRegistry

    # Priority 1-9: System commands (always first)
    registry.register(SystemCommandsAction())

    # Priority 10-49: User custom actions (loaded from config YAML)
    if config:
        _load_custom_actions(registry, config)

    # Priority 50: Shell command (fallback exec)
    registry.register(ShellAction())

    # Priority 100: AI assistant (generic, last resort)
    registry.register(AIAssistantAction())


def _load_custom_actions(registry, config: dict):
    """Load user-defined actions from YAML config."""
    custom_actions = config.get("actions", {}).get("custom", [])
    if not custom_actions:
        return

    for i, action_cfg in enumerate(custom_actions):
        name = action_cfg.get("name", f"custom_{i}")
        atype = action_cfg.get("type", "").lower()
        trigger = action_cfg.get("trigger", "")

        priority = action_cfg.get("priority", 20 + i)

        if atype == "http":
            from .http_action import HttpAction
            action = HttpAction(
                name=name,
                priority=priority,
                url=action_cfg.get("url", ""),
                method=action_cfg.get("method", "POST"),
                body_template=action_cfg.get("body_template", '{"text": "{text}"}'),
                trigger_keywords=action_cfg.get("trigger_keywords", []),
            )
        elif atype == "python":
            from .python_action import PythonAction
            action = PythonAction(
                name=name,
                priority=priority,
                script=action_cfg.get("script", ""),
                trigger_keywords=action_cfg.get("trigger_keywords", []),
            )
        elif atype == "keyboard":
            from .keyboard_action import KeyboardAction
            action = KeyboardAction(
                name=name,
                priority=priority,
                macro=action_cfg.get("macro", ""),
                trigger_keywords=action_cfg.get("trigger_keywords", []),
            )
        elif atype == "shell":
            from .shell_action import ShellAction
            action = ShellAction(
                name=name,
                priority=priority,
                command=action_cfg.get("command", ""),
                trigger_keywords=action_cfg.get("trigger_keywords", []),
            )
        else:
            continue

        registry.register(action)
