import time
import duckdb
from typing import Any
from mcp.duckdb_config import get_db_path, DUCKDB_TOOLS


def execute_query(tool_name: str, sql: str) -> dict[str, Any]:
    """
    Execute a SQL query against the DuckDB file mapped to tool_name.

    Returns a dict with the same structure as Google MCP Toolbox
    so the agent treats both servers identically:
    {
        "result":         list of row dicts,
        "query_used":     the SQL that was executed,
        "db_type":        "duckdb",
        "tool_name":      name of the tool called,
        "row_count":      number of rows returned,
        "execution_time": seconds taken,
        "error":          null on success, error message on failure
    }
    """
    tool = DUCKDB_TOOLS.get(tool_name)
    if tool is None:
        return _error_response(tool_name, sql, f"Unknown tool: '{tool_name}'")

    db_key = tool["db_key"]

    try:
        db_path = get_db_path(db_key)
    except (ValueError, FileNotFoundError) as e:
        return _error_response(tool_name, sql, str(e))

    # enforce read-only — never allow writes to benchmark data
    sql_upper = sql.strip().upper()
    if not _is_read_only(sql_upper):
        return _error_response(
            tool_name, sql,
            "Write operations are not permitted. Only SELECT queries are allowed."
        )

    start = time.perf_counter()
    try:
        # read_only=True prevents any accidental modification
        conn = duckdb.connect(str(db_path), read_only=True)
        relation = conn.execute(sql)
        cols = [d[0] for d in relation.description]
        rows = relation.fetchall()
        conn.close()

        elapsed = round(time.perf_counter() - start, 4)
        result  = [dict(zip(cols, row)) for row in rows]

        return {
            "result":         result,
            "query_used":     sql,
            "db_type":        "duckdb",
            "tool_name":      tool_name,
            "row_count":      len(result),
            "execution_time": elapsed,
            "error":          None,
        }

    except duckdb.Error as e:
        elapsed = round(time.perf_counter() - start, 4)
        return {
            "result":         [],
            "query_used":     sql,
            "db_type":        "duckdb",
            "tool_name":      tool_name,
            "row_count":      0,
            "execution_time": elapsed,
            "error":          str(e),
        }


def get_schema(tool_name: str) -> dict[str, Any]:
    """
    Return the full schema of the DuckDB database mapped to tool_name.
    Used by the schema introspector to populate AGENT.md and KB domain files.
    """
    tool = DUCKDB_TOOLS.get(tool_name)
    if tool is None:
        return _error_response(tool_name, "", f"Unknown tool: '{tool_name}'")

    db_key = tool["db_key"]

    try:
        db_path = get_db_path(db_key)
    except (ValueError, FileNotFoundError) as e:
        return _error_response(tool_name, "", str(e))

    try:
        conn   = duckdb.connect(str(db_path), read_only=True)
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'main'"
        ).fetchall()

        schema = {}
        for (tbl,) in tables:
            cols = conn.execute(
                f"SELECT column_name, data_type "
                f"FROM information_schema.columns "
                f"WHERE table_name = '{tbl}' "
                f"ORDER BY ordinal_position"
            ).fetchall()
            schema[tbl] = [
                {"column": col, "type": dtype}
                for col, dtype in cols
            ]

        conn.close()
        return {
            "tool_name": tool_name,
            "db_key":    db_key,
            "db_path":   str(db_path),
            "schema":    schema,
            "error":     None,
        }

    except duckdb.Error as e:
        return _error_response(tool_name, "", str(e))


def list_tools() -> list[dict[str, Any]]:
    """
    Return all available DuckDB tools with their descriptions.
    Called by the /v1/tools endpoint so the agent can discover tools.
    Matches the response format of Google MCP Toolbox v0.20.0.
    """
    return [
        {
            "name":        name,
            "description": meta["description"],
            "db_type":     "duckdb",
            "parameters":  [
                {
                    "name":        "sql",
                    "type":        "string",
                    "description": "SQL SELECT query to execute",
                    "required":    True,
                }
            ],
        }
        for name, meta in DUCKDB_TOOLS.items()
    ]


# ── helpers ───────────────────────────────────────────────────────────────────

def _is_read_only(sql_upper: str) -> bool:
    """Block any non-SELECT statement."""
    blocked = ("INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
               "ALTER", "TRUNCATE", "REPLACE", "MERGE")
    return sql_upper.startswith("SELECT") and not any(
        kw in sql_upper for kw in blocked
    )


def _error_response(tool_name: str, sql: str, msg: str) -> dict[str, Any]:
    return {
        "result":         [],
        "query_used":     sql,
        "db_type":        "duckdb",
        "tool_name":      tool_name,
        "row_count":      0,
        "execution_time": 0,
        "error":          msg,
    }