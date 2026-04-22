#!/usr/bin/env python3
"""Systematic regression suite for Intelligent Storage Nexus APIs."""

import os
import unittest

import requests

from api_server import parse_natural_language_query

BASE_URL = os.environ.get("ISN_TEST_BASE_URL", "http://localhost:8000").rstrip("/")
TIMEOUT_SEC = float(os.environ.get("ISN_TEST_TIMEOUT_SEC", "25"))


class APILiveRegressionTests(unittest.TestCase):
    """Regression tests against a running API server."""

    @classmethod
    def setUpClass(cls) -> None:
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=TIMEOUT_SEC)
            if response.status_code not in (200, 503):
                raise unittest.SkipTest(
                    f"API unavailable at {BASE_URL}: status={response.status_code}"
                )
        except requests.RequestException as exc:
            raise unittest.SkipTest(f"API unavailable at {BASE_URL}: {exc}") from exc

    def test_health_payload_shape(self) -> None:
        response = requests.get(f"{BASE_URL}/api/health", timeout=TIMEOUT_SEC)
        self.assertIn(response.status_code, (200, 503))
        payload = response.json()
        if response.status_code == 503:
            self.assertIn("detail", payload)
            self.assertIn("status", payload["detail"])
        else:
            self.assertIn("status", payload)
            self.assertIn("services", payload)

    def test_advanced_search_contract(self) -> None:
        response = requests.post(
            f"{BASE_URL}/api/search/advanced",
            json={"query": "python config parser", "limit": 5},
            timeout=TIMEOUT_SEC,
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("results", payload)
        self.assertIn("total", payload)
        self.assertIn("query", payload)
        self.assertIsInstance(payload["results"], list)
        self.assertIsInstance(payload["total"], int)

    def test_natural_search_contract(self) -> None:
        response = requests.post(
            f"{BASE_URL}/api/search/natural",
            json={"query": "large python files from last week", "limit": 5},
            timeout=TIMEOUT_SEC,
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("query", payload)
        self.assertIn("parsed_filters", payload)
        self.assertIn("results", payload)
        self.assertIn("total", payload)
        parsed_filters = payload["parsed_filters"]
        self.assertIn("extensions", parsed_filters)
        self.assertIn(".py", parsed_filters["extensions"])

    def test_files_endpoint_filters(self) -> None:
        response = requests.get(
            f"{BASE_URL}/api/files",
            params={"page": 1, "limit": 3, "category": "code", "q": "python"},
            timeout=TIMEOUT_SEC,
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("files", payload)
        self.assertIn("total", payload)
        self.assertIsInstance(payload["files"], list)
        self.assertIsInstance(payload["total"], int)

    def test_graph_query_and_status_endpoints(self) -> None:
        graph_query = requests.post(
            f"{BASE_URL}/api/graph/query",
            json={},
            timeout=TIMEOUT_SEC,
        )
        self.assertEqual(graph_query.status_code, 200)
        graph_payload = graph_query.json()
        self.assertIn("backend", graph_payload)

        graph_status = requests.get(
            f"{BASE_URL}/api/graph/status",
            timeout=TIMEOUT_SEC,
        )
        self.assertEqual(graph_status.status_code, 200)
        status_payload = graph_status.json()
        self.assertIn("backend", status_payload)
        self.assertIn("graph_built", status_payload)
        self.assertIn("build_in_progress", status_payload)

    def test_export_csv_contract(self) -> None:
        response = requests.get(
            f"{BASE_URL}/export/files",
            params={"format": "csv"},
            timeout=TIMEOUT_SEC,
        )
        self.assertEqual(response.status_code, 200)
        content_type = response.headers.get("content-type", "")
        self.assertIn("text/csv", content_type)

        lines = response.text.splitlines()
        self.assertGreaterEqual(len(lines), 1)
        self.assertIn("id", lines[0])
        self.assertIn("path", lines[0])


class NLParserUnitTests(unittest.IsolatedAsyncioTestCase):
    """Unit tests for deterministic natural-language parsing behavior."""

    async def test_rule_parser_handles_large_python_last_week(self) -> None:
        filters = await parse_natural_language_query(
            "large python files from last week"
        )
        self.assertIn(".py", filters["extensions"])
        self.assertGreaterEqual(filters.get("min_size_bytes") or 0, 1_000_000)
        self.assertIsNotNone(filters.get("date_after"))

    async def test_rule_parser_handles_numeric_constraints(self) -> None:
        filters = await parse_natural_language_query(
            "files smaller than 50 kb before 2025-01-01"
        )
        self.assertLessEqual(filters.get("max_size_bytes") or 0, 50 * 1024)
        self.assertEqual(filters.get("date_before"), "2025-01-01")


if __name__ == "__main__":
    unittest.main(verbosity=2)
