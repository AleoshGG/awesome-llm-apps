"""Session-level latency and Gemini usage accounting for the live demo."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from typing import Any


PRICING_SNAPSHOT = {
    "basis": "Gemini Developer API Standard paid tier",
    "effective_date": "2026-10-13",
    "currency": "USD",
    "unit": "per 1,000,000 tokens",
    "models": {
        "gemini-3.8-live": {
            "input": {"text": 0.75, "audio": 3.00, "image": 1.00, "video": 1.00},
            "output": {"text": 4.50, "audio": 12.00},
        },
        "gemini-3.8-flash": {
            "input": {"text": 0.75, "audio": 0.75, "image": 0.75, "video": 0.75},
            "output": {"text": 3.75},
            "valid_through": "2026-12-31",
        },
        "gemini-3.1-flash-image": {
            "input": {"text": 0.50, "image": 0.50},
            "output": {"text": 3.00, "image": 60.00},
        },
    },
}


def _plain(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True)
    return value


def _modality(value: Any) -> str:
    raw = getattr(value, "value", value)
    name = str(raw or "text").split(".")[-1].lower()
    return {"modality_unspecified": "text"}.get(name, name)


def _details(data: dict[str, Any], *names: str) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for name in names:
        for item in data.get(name, []) or []:
            item = _plain(item) or {}
            counts[_modality(item.get("modality"))] += int(item.get("token_count") or 0)
    return dict(counts)


def usage_record(source: str, model: str, metadata: Any) -> dict[str, Any] | None:
    """Normalize Live and GenerateContent usage metadata into one billable record."""

    data = _plain(metadata)
    if not isinstance(data, dict):
        return None

    inputs = _details(data, "prompt_tokens_details")
    prompt_total = int(data.get("prompt_token_count") or 0)
    if not inputs and prompt_total:
        inputs["text"] = prompt_total

    tool_inputs = _details(data, "tool_use_prompt_tokens_details")
    tool_total = int(data.get("tool_use_prompt_token_count") or 0)
    if not tool_inputs and tool_total:
        tool_inputs["text"] = tool_total
    for modality, count in tool_inputs.items():
        inputs[modality] = inputs.get(modality, 0) + count

    outputs = _details(data, "response_tokens_details", "candidates_tokens_details")
    response_total = int(data.get("response_token_count") or data.get("candidates_token_count") or 0)
    if not outputs and response_total:
        outputs["text"] = response_total

    thoughts = int(data.get("thoughts_token_count") or 0)
    if thoughts:
        outputs["text"] = outputs.get("text", 0) + thoughts

    if not inputs and not outputs:
        return None
    return {
        "source": source,
        "model": model,
        "input_tokens": inputs,
        "output_tokens": outputs,
        "reported_total_tokens": int(data.get("total_token_count") or 0),
    }


def _record_cost(record: dict[str, Any]) -> tuple[float | None, list[str]]:
    rates = PRICING_SNAPSHOT["models"].get(record["model"])
    if not rates:
        return None, [f"No pricing configured for {record['model']}"]
    cost = 0.0
    warnings = []
    for direction, key in (("input", "input_tokens"), ("output", "output_tokens")):
        for modality, count in record.get(key, {}).items():
            rate = rates.get(direction, {}).get(modality)
            if rate is None:
                warnings.append(f"No {direction} {modality} price for {record['model']}")
                continue
            cost += count * rate / 1_000_000
    return cost, warnings


def _percentile_nearest_rank(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(percentile * len(ordered)) - 1)]


def metrics_report(latencies: list[dict[str, Any]], usage: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [float(item["latency_ms"]) for item in latencies if item.get("valid", True)]
    by_source: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    total_cost = 0.0
    priced_records = 0

    for record in usage:
        source = str(record.get("source") or "unknown")
        summary = by_source.setdefault(source, {
            "input_tokens": defaultdict(int),
            "output_tokens": defaultdict(int),
            "cost_usd": 0.0,
            "records": 0,
        })
        for modality, count in record.get("input_tokens", {}).items():
            summary["input_tokens"][modality] += int(count)
        for modality, count in record.get("output_tokens", {}).items():
            summary["output_tokens"][modality] += int(count)
        cost, record_warnings = _record_cost(record)
        warnings.extend(record_warnings)
        if cost is not None:
            summary["cost_usd"] += cost
            total_cost += cost
            priced_records += 1
        summary["records"] += 1

    serialized_sources = {}
    for source, summary in by_source.items():
        serialized_sources[source] = {
            **summary,
            "input_tokens": dict(summary["input_tokens"]),
            "output_tokens": dict(summary["output_tokens"]),
            "cost_usd": round(summary["cost_usd"], 8),
        }

    return {
        "latency": {
            "definition": "last detected claimant voice sample to scheduled playback of first response audio",
            "valid_samples": len(valid),
            "samples_ms": [round(value, 1) for value in valid],
            "p50_ms": round(statistics.median(valid), 1) if valid else None,
            "p95_ms": round(_percentile_nearest_rank(valid, 0.95), 1) if valid else None,
            "method": {
                "minimum_speech_ms": 250,
                "silence_window_ms": 500,
                "threshold": "max(0.015, rolling noise floor x 3)",
                "percentile": "nearest rank",
            },
            "client": latencies[-1].get("client", {}) if latencies else {},
        },
        "usage_and_cost": {
            "by_source": serialized_sources,
            "total_cost_usd": round(total_cost, 8),
            "usage_records": len(usage),
            "priced_records": priced_records,
            "warnings": sorted(set(warnings)),
        },
        "pricing": PRICING_SNAPSHOT,
    }


__all__ = ["PRICING_SNAPSHOT", "metrics_report", "usage_record"]
