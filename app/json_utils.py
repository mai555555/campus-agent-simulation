from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import json


def json_default(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    raise TypeError(f"Object of type {value.__class__.__name__} is not JSON serializable")


def json_dumps(value, *args, **kwargs) -> str:
    kwargs.setdefault("default", json_default)
    return json.dumps(value, *args, **kwargs)
