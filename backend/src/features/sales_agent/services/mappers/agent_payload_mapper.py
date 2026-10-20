from dataclasses import asdict, is_dataclass
from datetime import datetime


def to_payload(value):
    if is_dataclass(value):
        return to_payload(asdict(value))
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: to_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_payload(item) for item in value]
    return value
