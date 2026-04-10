"""
Custom DuckDB MCP Server — port 5001
Mirrors the Google MCP Toolbox v0.20.0 HTTP interface so the agent
treats both servers identically.

Endpoints:
  GET  /v1/tools              — list all available DuckDB tools
  POST /v1/tools/{tool_name}  — execute a tool (run a SQL query)
  GET  /health                — server health + database file status
  GET  /schema/{tool_name}    — full schema for a DuckDB database
"""

import os
import sys
from pathlib import Path

# allow imports from the mcp/ folder regardless of where the
# server is started from
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from mcp.duckdb_tools import execute_query, get_schema, list_tools
from mcp.duckdb_config import list_databases, DUCKDB_TOOLS

# ── app setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Oracle Forge — DuckDB MCP Server",
    description="Custom MCP server for DuckDB databases in DataAgentBench",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── request / response models ─────────────────────────────────────────────────

class ToolRequest(BaseModel):
    sql: str


class ToolResponse(BaseModel):
    result:         list
    query_used:     str
    db_type:        str
    tool_name:      str
    row_count:      int
    execution_time: float
    error:          str | None


# ── endpoints ─────────────────────────────────────────────────────────────────

@app.get("/v1/tools")
def get_tools():
    """
    List all available DuckDB tools.
    Matches Google MCP Toolbox /v1/tools response format.
    """
    return {"tools": list_tools()}


@app.post("/v1/tools/{tool_name}", response_model=ToolResponse)
def invoke_tool(tool_name: str, req: ToolRequest):
    """
    Execute a DuckDB tool by name.
    Accepts: { "sql": "SELECT ..." }
    Returns: structured result matching Google MCP Toolbox format.
    """
    if tool_name not in DUCKDB_TOOLS:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found. "
                   f"Available tools: {list(DUCKDB_TOOLS.keys())}"
        )

    if not req.sql or not req.sql.strip():
        raise HTTPException(
            status_code=400,
            detail="SQL query cannot be empty."
        )

    result = execute_query(tool_name, req.sql)

    if result["error"]:
        # return 200 with error in body — same behaviour as Google MCP Toolbox
        # so the agent's self-correction loop can read and handle the error
        return result

    return result


@app.get("/health")
def health():
    """
    Server health check.
    Returns server status and existence status of all DuckDB files.
    """
    dbs     = list_databases()
    all_ok  = all(info["exists"] for info in dbs.values())

    return {
        "status":    "ok" if all_ok else "degraded",
        "server":    "duckdb-mcp",
        "port":      5001,
        "databases": dbs,
    }


@app.get("/schema/{tool_name}")
def schema(tool_name: str):
    """
    Return the full schema of the DuckDB database mapped to tool_name.
    Used by utils/schema_introspector.py to populate AGENT.md and KB files.
    """
    if tool_name not in DUCKDB_TOOLS:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found."
        )

    result = get_schema(tool_name)

    if result["error"]:
        raise HTTPException(
            status_code=500,
            detail=result["error"]
        )

    return result


@app.get("/")
def root():
    """Root endpoint — confirms server is running."""
    return {
        "server":      "Oracle Forge DuckDB MCP Server",
        "version":     "1.0.0",
        "port":        5001,
        "tools_count": len(DUCKDB_TOOLS),
        "tools":       list(DUCKDB_TOOLS.keys()),
        "docs":        "http://127.0.0.1:5001/docs",
    }


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("DUCKDB_MCP_PORT", "5001"))
    print(f"Starting DuckDB MCP Server on port {port}")
    print(f"Tools available: {list(DUCKDB_TOOLS.keys())}")
    uvicorn.run(
        "mcp.duckdb_server:app",
        host="127.0.0.1",
        port=port,
        reload=False,
        log_level="info",
    )