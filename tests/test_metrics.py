"""Deterministic tests for latency summaries and token pricing."""

import unittest

from live_demo.metrics import metrics_report, usage_record


class UsageTests(unittest.TestCase):
    def test_live_usage_keeps_modalities_and_tool_results(self):
        record = usage_record("live", "gemini-3.8-live", {
            "prompt_token_count": 1000,
            "prompt_tokens_details": [{"modality": "AUDIO", "token_count": 1000}],
            "tool_use_prompt_token_count": 20,
            "tool_use_prompt_tokens_details": [{"modality": "TEXT", "token_count": 20}],
            "response_token_count": 500,
            "response_tokens_details": [{"modality": "AUDIO", "token_count": 500}],
            "thoughts_token_count": 10,
            "total_token_count": 1530,
        })
        self.assertEqual(record["input_tokens"], {"audio": 1000, "text": 20})
        self.assertEqual(record["output_tokens"], {"audio": 500, "text": 10})

    def test_generate_content_field_names_are_supported(self):
        record = usage_record("workflow", "gemini-3.8-flash", {
            "prompt_token_count": 120,
            "candidates_token_count": 30,
            "candidates_tokens_details": [{"modality": "TEXT", "token_count": 30}],
        })
        self.assertEqual(record["input_tokens"], {"text": 120})
        self.assertEqual(record["output_tokens"], {"text": 30})

    def test_empty_metadata_is_ignored(self):
        self.assertIsNone(usage_record("live", "gemini-3.8-live", None))
        self.assertIsNone(usage_record("live", "gemini-3.8-live", {}))


class ReportTests(unittest.TestCase):
    def test_nearest_rank_latency_and_cost_breakdown(self):
        latencies = [{"latency_ms": value, "valid": True} for value in range(100, 1100, 100)]
        usage = [
            {
                "source": "live",
                "model": "gemini-3.8-live",
                "input_tokens": {"audio": 1000},
                "output_tokens": {"audio": 500},
            },
            {
                "source": "workflow",
                "model": "gemini-3.8-flash",
                "input_tokens": {"text": 1000},
                "output_tokens": {"text": 100},
            },
        ]
        report = metrics_report(latencies, usage)
        self.assertEqual(report["latency"]["p50_ms"], 550.0)
        self.assertEqual(report["latency"]["p95_ms"], 1000.0)
        self.assertEqual(report["usage_and_cost"]["by_source"]["live"]["cost_usd"], 0.009)
        self.assertEqual(report["usage_and_cost"]["total_cost_usd"], 0.010125)

    def test_unknown_model_is_reported_not_silently_priced(self):
        report = metrics_report([], [{
            "source": "live", "model": "unknown", "input_tokens": {"text": 10}, "output_tokens": {},
        }])
        self.assertEqual(report["usage_and_cost"]["priced_records"], 0)
        self.assertTrue(report["usage_and_cost"]["warnings"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
