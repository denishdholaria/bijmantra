from langchain_core.tools import tool
from src.db import run_query

@tool
async def list_tables_tool():
    """List all public tables in the database."""
    try:
        sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        rows = await run_query(sql)
        return [r['table_name'] for r in rows]
    except Exception as e:
        return f"Error listing tables: {str(e)}"

@tool
async def get_table_schema_tool(table_name: str):
    """Get the schema (columns, types) for a specific table."""
    try:
        sql = "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = 'public' AND table_name = $1"
        rows = await run_query(sql, [table_name])
        if not rows:
            return f"No schema found for table '{table_name}'. Check if it exists."
        return [dict(r) for r in rows]
    except Exception as e:
        return f"Error getting schema for {table_name}: {str(e)}"

@tool
async def run_query_tool(sql: str):
    """Execute a read-only SQL query against the database."""
    try:
        # Basic safety check
        if not sql.strip().lower().startswith("select"):
            return "Error: Only SELECT queries are allowed."
        
        limit_sql = sql if "limit" in sql.lower() else f"{sql} LIMIT 50"
        rows = await run_query(limit_sql)
        return [dict(r) for r in rows]
    except Exception as e:
        return f"Error executing query: {str(e)}"
