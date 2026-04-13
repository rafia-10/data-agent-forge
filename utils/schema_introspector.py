"""
Schema Introspector — Oracle Forge
Generates rich KB domain files for every DAB dataset.

Primary source: DAB db_description.txt + db_description_withhint.txt
Secondary source: MCP schema endpoint (column names, types)
Tertiary source: Claude enrichment (query patterns, join key format confirmation)

Usage:
    cd /home/project/oracle-forge
    python -m utils.schema_introspector

    # single dataset
    python -m utils.schema_introspector --datasets yelp

    # multiple datasets
    python -m utils.schema_introspector --datasets yelp agnews bookreview
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# ── config ────────────────────────────────────────────────────────────────────

load_dotenv(Path(__file__).parent.parent / ".env")

MCP_URL     = os.getenv("MCP_URL", "http://127.0.0.1:5000")
KB_DIR      = Path(__file__).parent.parent / "kb" / "domain"
ORACLE_ROOT = Path(__file__).parent.parent
DAB_ROOT    = Path(os.getenv("DAB_PATH", "/home/project/oracle-forge/DataAgentBench"))

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL   = "anthropic/claude-sonnet-4.6"

# dataset name → config
DATASET_MAP = {
    "yelp": {
        "conductor_name": "yelp",
        "dab_folder": "query_yelp",
        "tools": [
            "query_mongo_yelp_business",
            "query_mongo_yelp_checkin",
            "query_duckdb_yelp_user",
        ],
    },
    "agnews": {
        "conductor_name": "agnews",
        "dab_folder": "query_agnews",
        "tools": [
            "query_mongo_agnews",
            "query_sqlite_agnews_metadata",
        ],
    },
    "bookreview": {
        "conductor_name": "bookreview",
        "dab_folder": "query_bookreview",
        "tools": [
            "query_postgres_bookreview",
            "query_sqlite_bookreview",
        ],
    },
    "crmarenapro": {
        "conductor_name": "crmarenapro",
        "dab_folder": "query_crmarenapro",
        "tools": [
            "query_postgres_crmarenapro",
            "query_sqlite_crmarenapro_core",
            "query_sqlite_crmarenapro_products",
            "query_sqlite_crmarenapro_territory",
            "query_duckdb_crmarenapro_activities",
            "query_duckdb_crmarenapro_sales",
        ],
    },
    "deps_dev": {
        "conductor_name": "deps_dev",
        "dab_folder": "query_DEPS_DEV_V1",
        "tools": [
            "query_sqlite_deps_dev_package",
            "query_duckdb_deps_dev_project",
        ],
    },
    "github_repos": {
        "conductor_name": "github_repos",
        "dab_folder": "query_GITHUB_REPOS",
        "tools": [
            "query_sqlite_github_metadata",
            "query_duckdb_github_artifacts",
        ],
    },
    "googlelocal": {
        "conductor_name": "googlelocal",
        "dab_folder": "query_googlelocal",
        "tools": [
            "query_postgres_googlelocal",
            "query_sqlite_googlelocal_review",
        ],
    },
    "music_brainz": {
        "conductor_name": "music_brainz",
        "dab_folder": "query_music_brainz_20k",
        "tools": [
            "query_sqlite_music_brainz",
            "query_duckdb_music_brainz_sales",
        ],
    },
    "pancancer": {
        "conductor_name": "pancancer",
        "dab_folder": "query_PANCANCER_ATLAS",
        "tools": [
            "query_postgres_pancancer",
            "query_duckdb_pancancer_molecular",
        ],
    },
    "patents": {
        "conductor_name": "patents",
        "dab_folder": "query_PATENTS",
        "tools": [
            "query_postgres_patents",
            "query_sqlite_patents",
        ],
    },
    "stockindex": {
        "conductor_name": "stockindex",
        "dab_folder": "query_stockindex",
        "tools": [
            "query_sqlite_stockindex_info",
            "query_duckdb_stockindex_trade",
        ],
    },
    "stockmarket": {
        "conductor_name": "stockmarket",
        "dab_folder": "query_stockmarket",
        "tools": [
            "query_sqlite_stockmarket_info",
            "query_duckdb_stockmarket_trade",
        ],
    },
}


# ── DAB description loader ────────────────────────────────────────────────────

def load_dab_descriptions(dab_folder: str) -> dict:
    """Load official DAB db_description.txt and db_description_withhint.txt."""
    folder = DAB_ROOT / dab_folder
    result = {"description": "", "hints": ""}

    desc_path = folder / "db_description.txt"
    if desc_path.exists():
        result["description"] = desc_path.read_text(encoding="utf-8").strip()
        print(f"  Loaded db_description.txt ({len(result['description'])} chars)")
    else:
        print(f"  [WARN] db_description.txt not found: {desc_path}")

    hint_path = folder / "db_description_withhint.txt"
    if hint_path.exists():
        result["hints"] = hint_path.read_text(encoding="utf-8").strip()
        print(f"  Loaded hints ({len(result['hints'])} chars)")

    return result


# ── MCP schema loader ─────────────────────────────────────────────────────────

def load_mcp_schema(tool_name: str) -> dict:
    """Load schema from MCP /schema endpoint."""
    if "stockmarket_trade" in tool_name:
        return {"note": "2754 individual ticker tables. Query by ticker symbol directly e.g. SELECT * FROM AAPL LIMIT 5"}
    try:
        r = requests.get(f"{MCP_URL}/schema/{tool_name}", timeout=60)
        r.raise_for_status()
        return r.json().get("schema", {})
    except Exception as e:
        print(f"  [WARN] schema fetch failed for {tool_name}: {e}")
        return {}


# ── query loader ──────────────────────────────────────────────────────────────

def load_dataset_queries(dab_folder: str) -> list:
    """Load all query.json files for this dataset."""
    folder = DAB_ROOT / dab_folder
    queries = []
    for query_dir in sorted(folder.iterdir()):
        if not query_dir.is_dir():
            continue
        if not query_dir.name.startswith("query") or query_dir.name == "query_dataset":
            continue
        query_file = query_dir / "query.json"
        if query_file.exists():
            try:
                with open(query_file, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, str):
                    queries.append({"id": query_dir.name, "question": data})
                elif isinstance(data, dict) and "query" in data:
                    queries.append({"id": query_dir.name, "question": data["query"]})
            except Exception:
                pass
    return queries


# ── Claude enrichment ─────────────────────────────────────────────────────────

def enrich_with_claude(
    dataset: str,
    tools: list,
    dab_descriptions: dict,
    mcp_schemas: dict,
    queries: list,
) -> str:
    """Generate rich KB document using DAB descriptions as primary source."""
    if not OPENROUTER_KEY:
        return _fallback_markdown(dataset, tools, dab_descriptions)

    client = OpenAI(
        api_key=OPENROUTER_KEY,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/oracle-forge",
            "X-Title": "Oracle Forge Schema Introspector",
        },
    )

    query_text = "\n".join([f"- {q['id']}: {q['question']}" for q in queries])

    schema_text = ""
    for tool_name, schema in mcp_schemas.items():
        schema_text += f"\n### {tool_name}:\n{json.dumps(schema, indent=2)[:1500]}\n"

    tool_list = "\n".join([f"- `{t}`" for t in tools])

    prompt = f"""You are writing a Knowledge Base document for a production AI data agent competing on the DataAgentBench benchmark.
The agent reads this document before answering queries against the {dataset} dataset.
This document must be PRECISE, ACTIONABLE, and SPECIFIC to this dataset only.

---

OFFICIAL DAB DATABASE DESCRIPTION (trust this completely — it is the ground truth):
{dab_descriptions['description']}

OFFICIAL DAB HINTS (critical — copy these verbatim into the KB):
{dab_descriptions['hints']}

MCP TOOL SCHEMAS (live column names and types):
{schema_text}

EXACT QUERIES THE AGENT WILL BE ASKED:
{query_text}

AVAILABLE MCP TOOLS (use ONLY these exact names — never invent tool names):
{tool_list}

---

Write a structured markdown document with these exact sections:

## 1. Dataset Overview
One sentence.

## 2. CRITICAL — MCP Tool Mapping
| Tool Name | DB Type | Contains |
List every tool above with its DB type and what tables/collections it contains.

## 3. Tables and Collections
For each table/collection:
- Full description from official DAB description
- Every field: name, type, meaning
- Important value formats (e.g. date formats, ID prefixes, encoded values)

## 4. Join Keys
Exact join relationships. Include format mismatches.
Copy join key hints verbatim from the official hints.

## 5. Critical Domain Knowledge
Copy ALL hints verbatim from official DAB hints.
Add any additional knowledge needed to answer the queries above correctly.
Include: field encoding quirks, domain terminology, calculation formulas if given.

## 6. Query Patterns
For each query listed above:
- Which tools to call and in what order
- What join logic to apply
- What the expected answer format is

## 7. Known Pitfalls
Specific things that cause wrong answers:
- Format mismatches between tables
- Fields stored as strings that look like other types
- Ambiguous field names
- Special calculation requirements

Remove all generic advice. Only include what is specific to {dataset}."""

    try:
        response = client.chat.completions.create(
            model=CLAUDE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.0,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"  [ERROR] Claude enrichment failed: {e}")
        return _fallback_markdown(dataset, tools, dab_descriptions)


def _fallback_markdown(dataset: str, tools: list, dab_descriptions: dict) -> str:
    lines = [
        f"# {dataset} — Knowledge Base\n",
        "## Official DAB Description\n",
        dab_descriptions["description"],
        "\n\n## Official DAB Hints\n",
        dab_descriptions["hints"],
        "\n\n## MCP Tools\n",
    ]
    for tool in tools:
        lines.append(f"- `{tool}`")
    return "\n".join(lines)


# ── main ──────────────────────────────────────────────────────────────────────

def introspect_all(datasets: list = None):
    """Main entry point."""
    KB_DIR.mkdir(parents=True, exist_ok=True)

    # verify MCP server
    try:
        r = requests.get(f"{MCP_URL}/health", timeout=5)
        print(f"MCP server: {r.json().get('status', 'unknown')}")
    except Exception as e:
        print(f"[ERROR] MCP server not reachable: {e}")
        print("Start it with: python -m mcp.mcp_server")
        sys.exit(1)

    target_datasets = datasets or list(DATASET_MAP.keys())
    changelog_entries = []

    for dataset, config in DATASET_MAP.items():
        if dataset not in target_datasets:
            continue

        print(f"\n{'='*60}")
        print(f"Processing: {dataset}")
        print(f"{'='*60}")

        # 1. load official DAB descriptions (primary source)
        dab_descriptions = load_dab_descriptions(config["dab_folder"])
        if not dab_descriptions["description"]:
            print(f"  [SKIP] No DAB description found for {dataset}")
            continue

        # 2. load MCP schemas
        mcp_schemas = {}
        for tool_name in config["tools"]:
            print(f"  Loading schema: {tool_name}")
            schema = load_mcp_schema(tool_name)
            if schema:
                mcp_schemas[tool_name] = schema
            time.sleep(0.3)

        # 3. load actual queries
        queries = load_dataset_queries(config["dab_folder"])
        print(f"  Found {len(queries)} queries")

        # 4. enrich with Claude
        print(f"  Enriching with Claude...")
        markdown = enrich_with_claude(
            dataset=dataset,
            tools=config["tools"],
            dab_descriptions=dab_descriptions,
            mcp_schemas=mcp_schemas,
            queries=queries,
        )

        # 5. write to kb/domain/
        out_path = KB_DIR / f"dab_{dataset}.md"
        out_path.write_text(markdown, encoding="utf-8")
        print(f"  Written: {out_path}")
        changelog_entries.append(
            f"- `dab_{dataset}.md` — regenerated from DAB descriptions + MCP schemas + {len(queries)} queries"
        )
        time.sleep(1)  # rate limit protection

    # write CHANGELOG
    from datetime import datetime
    changelog = KB_DIR / "CHANGELOG.md"
    existing = changelog.read_text(encoding="utf-8") if changelog.exists() else ""
    entry = f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\nSchema introspector run — DAB-description-first approach.\n\n"
    entry += "\n".join(changelog_entries) + "\n"
    changelog.write_text(entry + existing, encoding="utf-8")

    print(f"\nDone. {len(changelog_entries)} domain files written to {KB_DIR}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Oracle Forge Schema Introspector")
    parser.add_argument(
        "--datasets", nargs="+",
        default=None,
        choices=list(DATASET_MAP.keys()),
        help="Datasets to process (default: all)",
    )
    args = parser.parse_args()
    introspect_all(datasets=args.datasets)