"""Console plus JSON-lines structured logging."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path


class JsonFormatter(logging.Formatter):
    RESERVED = set(logging.LogRecord(None, 0, "", 0, "", (), None).__dict__)

    def format(self, record: logging.LogRecord) -> str:
        item = {
            "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
            "level": record.levelname,
            "event": getattr(record, "event", record.name),
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in self.RESERVED and key not in {"message", "asctime", "event"}:
                try:
                    json.dumps(value)
                    item[key] = value
                except TypeError:
                    item[key] = str(value)
        if record.exc_info:
            item["exception"] = self.formatException(record.exc_info)
        return json.dumps(item, ensure_ascii=False)


def configure_logging(level: str = "INFO", filename: str = "logs/nova.jsonl", debug: bool = False) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.DEBUG if debug else getattr(logging, level.upper(), logging.INFO))
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root.addHandler(console)
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(path, encoding="utf-8")
    file_handler.setFormatter(JsonFormatter())
    root.addHandler(file_handler)


def log_event(logger: logging.Logger, event: str, **fields: object) -> None:
    logger.info(event, extra={"event": event, **fields})
