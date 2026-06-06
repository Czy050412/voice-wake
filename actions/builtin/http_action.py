# -*- coding: utf-8 -*-
"""HTTP webhook action — send recognized text to any API endpoint."""
import json
from ..base import BaseAction, ActionResult


class HttpAction(BaseAction):
    """POST recognized text to any HTTP endpoint. For IFTTT, Home Assistant, custom servers, etc."""

    name = "http"
    priority = 20

    def __init__(self, name="http", priority=20, url="", method="POST",
                 body_template='{"text": "{text}"}', trigger_keywords=None):
        self.name = name
        self.priority = priority
        self._url = url
        self._method = method.upper()
        self._template = body_template
        self._keywords = trigger_keywords or []

    def can_handle(self, text: str) -> bool:
        if not self._url or not self._keywords:
            return False
        return any(kw in text for kw in self._keywords)

    def execute(self, text: str) -> ActionResult:
        import urllib.request
        import urllib.error

        body = self._template.replace("{text}", text)
        req = urllib.request.Request(
            self._url,
            data=body.encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method=self._method
        )
        try:
            resp = urllib.request.urlopen(req, timeout=5)
            return ActionResult(handled=True, action_name=self.name, success=True,
                                message=f"HTTP {resp.status}")
        except urllib.error.HTTPError as e:
            return ActionResult(handled=True, action_name=self.name, success=False,
                                message=f"HTTP {e.code}")
        except Exception as e:
            return ActionResult(handled=True, action_name=self.name, success=False,
                                message=str(e)[:100])
