import json
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"


def _write_log(entry: dict):
    line = json.dumps(entry, default=str)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        # swallow logging errors
        pass


def log_json(level: str, message: str, **kwargs: Any):
    entry = {
        "level": level.upper(),
        "message": message,
        "ts": datetime.utcnow().isoformat() + "Z",
    }
    entry.update(kwargs)
    print(json.dumps(entry))
    _write_log(entry)


def log_route(func: Callable) -> Callable:
    is_coroutine = asyncio.iscoroutinefunction(func)

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        request = kwargs.get("request") or (args[0] if args else None)
        endpoint = getattr(request, "url", None)
        start = time.perf_counter()
        try:
          result = await func(*args, **kwargs)
          return result
        finally:
          duration = (time.perf_counter() - start) * 1000
          log_json(
              "INFO",
              "route_executed",
              endpoint=str(endpoint) if endpoint else func.__name__,
              duration_ms=round(duration, 2),
              request_id=getattr(request, "state", {}).get("request_id", None)
          )

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        request = kwargs.get("request") or (args[0] if args else None)
        endpoint = getattr(request, "url", None)
        start = time.perf_counter()
        try:
          return func(*args, **kwargs)
        finally:
          duration = (time.perf_counter() - start) * 1000
          log_json(
              "INFO",
              "route_executed",
              endpoint=str(endpoint) if endpoint else func.__name__,
              duration_ms=round(duration, 2),
              request_id=getattr(request, "state", {}).get("request_id", None)
          )

    return async_wrapper if is_coroutine else sync_wrapper


# ensure asyncio imported
import asyncio  # noqa: E402




