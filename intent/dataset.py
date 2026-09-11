"""Dataset IO for intent examples."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class IntentExample(BaseModel):
    text: str = Field(min_length=1)
    intent: str = Field(min_length=1)
    entities: dict[str, Any] = Field(default_factory=dict)


def load_examples(path: str | Path) -> list[IntentExample]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("examples", [])
    return [IntentExample.model_validate(item) for item in data]

