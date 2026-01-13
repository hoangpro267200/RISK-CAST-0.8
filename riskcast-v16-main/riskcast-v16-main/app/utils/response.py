from datetime import datetime
from typing import Any, Optional, Union


def envelope(ok: bool, data: Optional[Any] = None, error: Optional[str] = None) -> dict:
    return {
        "ok": ok,
        "data": data if ok else None,
        "error": None if ok else (error or "unknown_error"),
        "ts": datetime.utcnow().isoformat() + "Z",
    }


def success(data: Any) -> dict:
    return envelope(True, data=data)


def failure(error: Union[str, Exception]) -> dict:
    message = str(error) if not isinstance(error, str) else error
    return envelope(False, error=message)




