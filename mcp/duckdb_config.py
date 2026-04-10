import os
from pathlib import Path

DAB_PATH = os.getenv(
    "DAB_PATH",
    "/home/project/oracle-forge/DataAgentBench"
)

# Every DuckDB file across all 12 DAB datasets
# Key   = logical name the agent uses to identify the database
# Value = absolute path to the .duckdb file on the server

DUCKDB_DATABASES = {
    "crmarenapro_activities": Path(DAB_PATH) / "query_crmarenapro" / "query_dataset" / "activities.duckdb",
    "crmarenapro_sales":      Path(DAB_PATH) / "query_crmarenapro" / "query_dataset" / "sales_pipeline.duckdb",
    "music_brainz_sales":     Path(DAB_PATH) / "query_music_brainz_20k" / "query_dataset" / "sales.duckdb",
}

# Tool definitions exposed to the agent
# Each entry maps to one DuckDB file
# The agent reads the description to decide which tool to call

DUCKDB_TOOLS = {
    "query_duckdb_crmarenapro_activities": {
        "db_key":      "crmarenapro_activities",
        "description": (
            "Query the crmarenapro activities DuckDB database. "
            "Contains sales activity records including calls, emails, "
            "meetings and their outcomes linked to CRM accounts."
        ),
    },
    "query_duckdb_crmarenapro_sales": {
        "db_key":      "crmarenapro_sales",
        "description": (
            "Query the crmarenapro sales pipeline DuckDB database. "
            "Contains sales pipeline stages, deal values, "
            "probability scores and forecast data."
        ),
    },
    "query_duckdb_music_brainz_sales": {
        "db_key":      "music_brainz_sales",
        "description": (
            "Query the music brainz sales DuckDB database. "
            "Contains music sales data including track sales figures, "
            "revenue and platform distribution."
        ),
    },
}


def get_db_path(db_key: str) -> Path:
    """Return the file path for a given DuckDB database key."""
    path = DUCKDB_DATABASES.get(db_key)
    if path is None:
        raise ValueError(f"Unknown DuckDB database key: '{db_key}'")
    if not path.exists():
        raise FileNotFoundError(
            f"DuckDB file not found at {path}. "
            f"Check DAB_PATH is set correctly: {DAB_PATH}"
        )
    return path


def list_databases() -> dict:
    """Return all registered DuckDB databases with their existence status."""
    return {
        key: {
            "path":   str(path),
            "exists": path.exists(),
        }
        for key, path in DUCKDB_DATABASES.items()
    }