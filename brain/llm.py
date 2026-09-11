"""Optional Ollama JSON adapter. Its output is always validated by Pydantic."""

from __future__ import annotations

import json
from urllib import request

from .schemas import ActionPlan


SYSTEM_PROMPT = """Convert the Thai or English Windows command into JSON only.
Schema: {"actions":[{"type":"allowed_action","target":"optional","parameters":{}}],"response":null}
Allowed actions: open_app, close_app, open_project, open_folder, open_url, web_search,
volume_up, volume_down, set_volume, mute, unmute, media_play, media_pause, media_next,
media_previous, screenshot, lock_pc, restart, shutdown, get_time, get_system_info, unknown.
Never produce shell commands. Maximum 8 actions."""


class OllamaClient:
    def __init__(self, url: str, model: str, timeout_seconds: float = 20) -> None:
        self.url = url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def parse(self, text: str) -> ActionPlan:
        payload = json.dumps(
            {"model": self.model, "format": "json", "stream": False,
             "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                          {"role": "user", "content": text}]}
        ).encode()
        req = request.Request(
            f"{self.url}/api/chat", data=payload,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with request.urlopen(req, timeout=self.timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body.get("message", {}).get("content", "")
        return ActionPlan.model_validate_json(content)

