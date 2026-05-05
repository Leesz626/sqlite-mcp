"""SQLite MCP Server - Full-featured SQLite database interaction via MCP protocol."""
import os
import sys
import sqlite3
import json
import argparse
from pathlib import Path
from mcp.server.fastmcp import FastMCP


def resolve_db_path(db_path: str | None = None, default_fallback: str = "database.db") -> str:
    """Resolve database path relative to CWD (project workspace).
    
    Priority: tool argument > SQLITE_DB_PATH env > CLI --db > default fallback.
    Path traversal (..) is blocked.
    """
    resolved = _default_db or db_path or os.environ.get("SQLITE_DB_PATH") or default_fallback
    p = Path(resolved)
    if ".." in p.parts:
        raise ValueError(f"Path traversal not allowed: {resolved}")
    return str(p.resolve())


def get_connection(db_path: str, readonly: bool = False) -> sqlite3.Connection:
    """Open a SQLite connection with row factory for dict-like access."""
    uri = f"file:{db_path}?mode=ro" if readonly else db_path
    conn = sqlite3.connect(uri if readonly else db_path, uri=readonly)
    conn.row_factory = sqlite3.Row
    if not readonly:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
    return conn


# CLI argument for default database
_default_db: str | None = None

parser = argparse.ArgumentParser(description="SQLite MCP Server")
parser.add_argument("--db", type=str, default=None, help="Default database file path")
_args, _ = parser.parse_known_args()
_default_db = _args.db

mcp = FastMCP("sqlite")


@mcp.tool()
def sqlite_query(sql: str, db_path: str | None = None) -> str:
    """Run a read-only SELECT query on a SQLite database.

    Args:
        sql: SQL SELECT statement to execute
        db_path: Path to database file (relative to workspace, default: database.db)

    Returns:
        JSON array of result rows with row count
    """
    resolved = resolve_db_path(db_path)
    if not os.path.exists(resolved):
        return f"Error: Database file not found: {resolved}"

    try:
        conn = get_connection(resolved, readonly=True)
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        conn.close()
        return json.dumps({
            "row_count": len(rows),
            "rows": [dict(r) for r in rows]
        }, ensure_ascii=False, indent=2, default=str)
    except sqlite3.Error as e:
        return f"SQLite error: {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def sqlite_execute(sql: str, db_path: str | None = None) -> str:
    """Execute one or more SQL statements (INSERT/UPDATE/DELETE/DDL).

    Args:
        sql: SQL statement(s) to execute. Multiple statements separated by semicolons are supported.
        db_path: Path to database file (relative to workspace, default: database.db)

    Returns:
        Affected row count or success message for DDL
    """
    resolved = resolve_db_path(db_path)

    try:
        conn = get_connection(resolved)
        try:
            statements = [s.strip() for s in sql.split(";") if s.strip()]

            for stmt in statements:
                conn.execute(stmt)

            conn.commit()
            total = conn.total_changes
            conn.close()
            return json.dumps({
                "success": True,
                "statements_executed": len(statements),
                "total_changes": total,
            }, indent=2)
        except sqlite3.Error as e:
            conn.rollback()
            conn.close()
            return f"SQLite error (transaction rolled back): {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def sqlite_list_tables(db_path: str | None = None) -> str:
    """List all tables in the SQLite database.

    Args:
        db_path: Path to database file (relative to workspace, default: database.db)

    Returns:
        JSON array of table names
    """
    resolved = resolve_db_path(db_path)
    if not os.path.exists(resolved):
        return f"Error: Database file not found: {resolved}"

    try:
        conn = get_connection(resolved, readonly=True)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = [row["name"] for row in cursor.fetchall()]
        conn.close()
        return json.dumps({"tables": tables, "count": len(tables)}, indent=2)
    except sqlite3.Error as e:
        return f"SQLite error: {e}"


@mcp.tool()
def sqlite_describe_table(table: str, db_path: str | None = None) -> str:
    """Describe the schema of a specific table.

    Args:
        table: Table name to describe
        db_path: Path to database file (relative to workspace, default: database.db)

    Returns:
        Column definitions and CREATE TABLE SQL
    """
    resolved = resolve_db_path(db_path)
    if not os.path.exists(resolved):
        return f"Error: Database file not found: {resolved}"

    try:
        conn = get_connection(resolved, readonly=True)
        cursor = conn.execute(f"PRAGMA table_info({table})")
        columns = [dict(row) for row in cursor.fetchall()]
        cursor = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        row = cursor.fetchone()
        create_sql = row["sql"] if row else None
        conn.close()

        return json.dumps({
            "table": table,
            "columns": columns,
            "create_sql": create_sql,
        }, ensure_ascii=False, indent=2)
    except sqlite3.Error as e:
        return f"SQLite error: {e}"


@mcp.tool()
def sqlite_export_table(table: str, db_path: str | None = None, limit: int = 1000) -> str:
    """Export table rows as JSON.

    Args:
        table: Table name to export
        db_path: Path to database file (relative to workspace, default: database.db)
        limit: Maximum rows to export (default: 1000)

    Returns:
        JSON array of row objects
    """
    resolved = resolve_db_path(db_path)
    if not os.path.exists(resolved):
        return f"Error: Database file not found: {resolved}"

    try:
        conn = get_connection(resolved, readonly=True)
        cursor = conn.execute(f"SELECT * FROM {table} LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return json.dumps({
            "table": table,
            "row_count": len(rows),
            "rows": [dict(r) for r in rows],
        }, ensure_ascii=False, indent=2, default=str)
    except sqlite3.Error as e:
        return f"SQLite error: {e}"


@mcp.tool()
def sqlite_import_json(table: str, data: str, db_path: str | None = None) -> str:
    """Import JSON array data into a table.

    Args:
        table: Target table name
        data: JSON array string of row objects. Keys must match column names.
        db_path: Path to database file (relative to workspace, default: database.db)

    Returns:
        Count of inserted rows
    """
    resolved = resolve_db_path(db_path)

    try:
        rows = json.loads(data)
        if not isinstance(rows, list):
            return "Error: data must be a JSON array of objects"

        conn = get_connection(resolved)
        try:
            inserted = 0
            for row in rows:
                columns = list(row.keys())
                placeholders = ", ".join(["?" for _ in columns])
                values = [row[c] for c in columns]
                cols_str = ", ".join(columns)
                conn.execute(
                    f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})",
                    values
                )
                inserted += 1

            conn.commit()
            conn.close()
            return json.dumps({
                "success": True,
                "table": table,
                "inserted": inserted,
            }, indent=2)
        except sqlite3.Error as e:
            conn.rollback()
            conn.close()
            return f"SQLite error (rolled back): {e}"
    except json.JSONDecodeError as e:
        return f"JSON parse error: {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def sqlite_transaction(statements: list[str], db_path: str | None = None) -> str:
    """Execute multiple SQL statements in a single transaction.

    All statements succeed or all roll back (atomic).

    Args:
        statements: List of SQL statements to execute atomically
        db_path: Path to database file (relative to workspace, default: database.db)

    Returns:
        Success message with statement count
    """
    resolved = resolve_db_path(db_path)

    try:
        conn = get_connection(resolved)
        try:
            for stmt in statements:
                conn.execute(stmt)
            conn.commit()
            conn.close()
            return json.dumps({
                "success": True,
                "statements_executed": len(statements),
            }, indent=2)
        except sqlite3.Error as e:
            conn.rollback()
            conn.close()
            return f"SQLite error (transaction rolled back): {e}"
    except Exception as e:
        return f"Error: {e}"


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
