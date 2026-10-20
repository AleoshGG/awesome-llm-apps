from dataclasses import dataclass


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    name: str
    output: dict
    is_error: bool = False
