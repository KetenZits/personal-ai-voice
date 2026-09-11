"""Routes natural-language input to the local classifier, then optional local LLM."""

from __future__ import annotations

import logging

from .schemas import ActionPlan, ActionType


class BrainRouter:
    def __init__(self, parser: object, llm: object | None = None) -> None:
        self.parser = parser
        self.llm = llm
        self.log = logging.getLogger(__name__)

    def route(self, text: str) -> ActionPlan:
        plan = self.parser.parse(text)
        needs_llm = not plan.actions or any(a.type == ActionType.UNKNOWN for a in plan.actions)
        if needs_llm and self.llm is not None:
            try:
                return self.llm.parse(text)
            except Exception as exc:  # local LLM is an optional fallback
                self.log.warning("Local LLM failed; returning classifier result", extra={"error": str(exc)})
        return plan

