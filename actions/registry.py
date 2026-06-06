# -*- coding: utf-8 -*-
"""
Action Registry — plug-in dispatcher.
Routes recognized speech through a priority-ordered pipeline of actions.
"""
import os
import sys
import time
import logging
from typing import List

from .base import BaseAction, ActionResult

logger = logging.getLogger("voice_wake.actions")


class ActionRegistry:
    """Ordered pipeline of actions. Tries each in priority order until one handles."""

    def __init__(self):
        self._actions: List[BaseAction] = []
        self._loaded = False

    def register(self, action: BaseAction):
        """Register an action, maintaining priority order."""
        self._actions.append(action)
        self._actions.sort(key=lambda a: a.priority)

    def remove(self, name: str):
        """Remove an action by name."""
        self._actions = [a for a in self._actions if a.name != name]

    def dispatch(self, text: str) -> ActionResult:
        """Try each action in priority order. First to claim text wins."""
        for action in self._actions:
            try:
                if action.can_handle(text):
                    result = action.execute(text)
                    if result.handled:
                        logger.debug(f"Action [{action.name}] handled: {text[:60]}")
                        return result
            except Exception as e:
                logger.warning(f"Action [{action.name}] error: {e}")
        return ActionResult(handled=False)

    @property
    def actions(self) -> List[BaseAction]:
        return list(self._actions)

    def list_actions(self) -> list:
        """Return [(name, priority, doc)] for all registered actions."""
        return [(a.name, a.priority, a.__doc__ or "") for a in self._actions]


# Global singleton
action_registry = ActionRegistry()
