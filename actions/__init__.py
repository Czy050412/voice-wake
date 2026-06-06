# Voice Wake v3 - Pluggable Action System
# "Unlimited possibilities" — any Python script, HTTP call, shell command, or keyboard macro.
from .base import BaseAction, ActionResult
from .registry import ActionRegistry, action_registry
from .builtin import load_builtins
