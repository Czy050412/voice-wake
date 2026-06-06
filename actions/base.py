# -*- coding: utf-8 -*-
"""
Base action class — all plugin actions inherit from this.
Each action receives recognized text and returns an ActionResult.
"""
from dataclasses import dataclass, field
from typing import Optional, Callable, Any


@dataclass
class ActionResult:
    """Result of an action execution."""
    handled: bool = False
    action_name: str = ""
    success: bool = False
    message: str = ""
    data: Any = None


class BaseAction:
    """Plug-in action base. Override `execute(text)` in subclasses."""

    name: str = "base"
    priority: int = 100  # Lower = higher priority (1 = first to try)
    _condition: Optional[Callable] = None

    def can_handle(self, text: str) -> bool:
        """Check if this action should handle the given text."""
        if self._condition:
            return self._condition(text)
        return False

    def execute(self, text: str) -> ActionResult:
        """Execute the action. Must be overridden."""
        raise NotImplementedError("Subclasses must implement execute()")

    def __repr__(self):
        return f"<{self.__class__.__name__} name='{self.name}' pri={self.priority}>"
