"""
Tests for utils/schema_introspector.py

Tests cover the pure-logic functions that do not require a live MCP server
or Claude API. Network-dependent functions are tested with mocked requests.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── import helpers ────────────────────────────────────────────────────────────

from utils.schema_introspector import (
    _fallback_markdown,
    load_dab_descriptions,
    load_dataset_queries,
    load_mcp_schema,
    DATASET_MAP,
)


# ── _fallback_markdown ────────────────────────────────────────────────────────

class TestFallbackMarkdown:
    def test_contains_dataset_name(self):
        md = _fallback_markdown(
            dataset="yelp",
            tools=["query_mongo_yelp_business"],
            dab_descriptions={"description": "Yelp business data.", "hints": ""},
        )
        assert "yelp" in md

    def test_contains_all_tool_names(self):
        tools = ["query_mongo_yelp_business", "query_duckdb_yelp_user"]
        md = _fallback_markdown(
            dataset="yelp",
            tools=tools,
            dab_descriptions={"description": "desc", "hints": "hint text"},
        )
        for tool in tools:
            assert tool in md

    def test_contains_dab_description(self):
        md = _fallback_markdown(
            dataset="yelp",
            tools=[],
            dab_descriptions={"description": "This is the official description.", "hints": ""},
        )
        assert "This is the official description." in md

    def test_contains_dab_hints(self):
        md = _fallback_markdown(
            dataset="yelp",
            tools=[],
            dab_descriptions={"description": "", "hints": "Join on businessref_ prefix."},
        )
        assert "Join on businessref_ prefix." in md

    def test_empty_tools_produces_valid_markdown(self):
        md = _fallback_markdown("test_ds", [], {"description": "", "hints": ""})
        assert isinstance(md, str)
        assert len(md) > 0


# ── load_dab_descriptions ─────────────────────────────────────────────────────

class TestLoadDabDescriptions:
    def test_returns_empty_strings_when_folder_missing(self, tmp_path):
        with patch("utils.schema_introspector.DAB_ROOT", tmp_path):
            result = load_dab_descriptions("query_missing_dataset")
        assert result["description"] == ""
        assert result["hints"] == ""

    def test_loads_description_file(self, tmp_path):
        folder = tmp_path / "query_yelp"
        folder.mkdir()
        (folder / "db_description.txt").write_text("Yelp business reviews.", encoding="utf-8")
        with patch("utils.schema_introspector.DAB_ROOT", tmp_path):
            result = load_dab_descriptions("query_yelp")
        assert result["description"] == "Yelp business reviews."

    def test_loads_hints_file(self, tmp_path):
        folder = tmp_path / "query_yelp"
        folder.mkdir()
        (folder / "db_description.txt").write_text("desc", encoding="utf-8")
        (folder / "db_description_withhint.txt").write_text("Use regex for location.", encoding="utf-8")
        with patch("utils.schema_introspector.DAB_ROOT", tmp_path):
            result = load_dab_descriptions("query_yelp")
        assert result["hints"] == "Use regex for location."

    def test_hints_empty_when_file_missing(self, tmp_path):
        folder = tmp_path / "query_yelp"
        folder.mkdir()
        (folder / "db_description.txt").write_text("desc", encoding="utf-8")
        with patch("utils.schema_introspector.DAB_ROOT", tmp_path):
            result = load_dab_descriptions("query_yelp")
        assert result["hints"] == ""

    def test_strips_whitespace(self, tmp_path):
        folder = tmp_path / "query_yelp"
        folder.mkdir()
        (folder / "db_description.txt").write_text("  desc with spaces  \n\n", encoding="utf-8")
        with patch("utils.schema_introspector.DAB_ROOT", tmp_path):
            result = load_dab_descriptions("query_yelp")
        assert result["description"] == "desc with spaces"


# ── load_dataset_queries ──────────────────────────────────────────────────────

class TestLoadDatasetQueries:
    def test_returns_empty_list_when_folder_missing(self, tmp_path):
        with patch("utils.schema_introspector.DAB_ROOT", tmp_path):
            result = load_dataset_queries("query_missing")
        assert result == []

    def test_loads_string_query_json(self, tmp_path):
        folder = tmp_path / "query_yelp"
        q1 = folder / "query1"
        q1.mkdir(parents=True)
        (q1 / "query.json").write_text('"What is the average rating?"', encoding="utf-8")
        with patch("utils.schema_introspector.DAB_ROOT", tmp_path):
            result = load_dataset_queries("query_yelp")
        assert len(result) == 1
        assert result[0]["question"] == "What is the average rating?"
        assert result[0]["id"] == "query1"

    def test_loads_dict_query_json(self, tmp_path):
        folder = tmp_path / "query_yelp"
        q1 = folder / "query1"
        q1.mkdir(parents=True)
        (q1 / "query.json").write_text(
            json.dumps({"query": "Which city has the most reviews?"}),
            encoding="utf-8"
        )
        with patch("utils.schema_introspector.DAB_ROOT", tmp_path):
            result = load_dataset_queries("query_yelp")
        assert result[0]["question"] == "Which city has the most reviews?"

    def test_skips_query_dataset_directory(self, tmp_path):
        folder = tmp_path / "query_yelp"
        bad = folder / "query_dataset"
        bad.mkdir(parents=True)
        (bad / "query.json").write_text('"should be skipped"', encoding="utf-8")
        with patch("utils.schema_introspector.DAB_ROOT", tmp_path):
            result = load_dataset_queries("query_yelp")
        assert result == []

    def test_loads_multiple_queries_sorted(self, tmp_path):
        folder = tmp_path / "query_yelp"
        for i in [3, 1, 2]:
            q = folder / f"query{i}"
            q.mkdir(parents=True)
            (q / "query.json").write_text(f'"Question {i}"', encoding="utf-8")
        with patch("utils.schema_introspector.DAB_ROOT", tmp_path):
            result = load_dataset_queries("query_yelp")
        ids = [r["id"] for r in result]
        assert ids == sorted(ids)


# ── load_mcp_schema ───────────────────────────────────────────────────────────

class TestLoadMcpSchema:
    def test_stockmarket_trade_returns_hardcoded_note(self):
        result = load_mcp_schema("query_duckdb_stockmarket_trade")
        assert "note" in result
        assert "2754" in result["note"]

    def test_successful_mcp_response(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"schema": {"tables": ["review"]}}
        mock_response.raise_for_status = MagicMock()
        with patch("utils.schema_introspector.requests.get", return_value=mock_response):
            result = load_mcp_schema("query_duckdb_yelp_user")
        assert result == {"tables": ["review"]}

    def test_connection_error_returns_empty_dict(self):
        with patch("utils.schema_introspector.requests.get", side_effect=ConnectionError("refused")):
            result = load_mcp_schema("query_postgres_bookreview")
        assert result == {}

    def test_timeout_returns_empty_dict(self):
        import requests as req
        with patch("utils.schema_introspector.requests.get", side_effect=req.exceptions.Timeout()):
            result = load_mcp_schema("query_sqlite_patents")
        assert result == {}


# ── DATASET_MAP ───────────────────────────────────────────────────────────────

class TestDatasetMap:
    def test_all_12_datasets_present(self):
        expected = {
            "yelp", "agnews", "bookreview", "crmarenapro",
            "deps_dev", "github_repos", "googlelocal", "music_brainz",
            "pancancer", "patents", "stockindex", "stockmarket",
        }
        assert set(DATASET_MAP.keys()) == expected

    def test_every_dataset_has_required_keys(self):
        for name, config in DATASET_MAP.items():
            assert "conductor_name" in config, f"{name} missing conductor_name"
            assert "dab_folder" in config,    f"{name} missing dab_folder"
            assert "tools" in config,         f"{name} missing tools"
            assert len(config["tools"]) >= 1, f"{name} has no tools"

    def test_crmarenapro_has_most_tools(self):
        assert len(DATASET_MAP["crmarenapro"]["tools"]) == 6

    def test_tool_names_are_strings(self):
        for name, config in DATASET_MAP.items():
            for tool in config["tools"]:
                assert isinstance(tool, str), f"{name} tool {tool!r} is not a string"
                assert tool.startswith("query_"), f"{name} tool {tool!r} does not start with query_"
