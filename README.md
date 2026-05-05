# sqlite-mcp-server

A full-featured SQLite MCP server for AI agents. Supports query, execute, DDL, import/export, transactions, and more.

## Features

- **Read-only queries** (`sqlite_query`) - Safe SELECT with row-level result output
- **Write operations** (`sqlite_execute`) - INSERT, UPDATE, DELETE, DDL (multi-statement)  
- **Table discovery** (`sqlite_list_tables`) - List all tables in the database
- **Schema inspection** (`sqlite_describe_table`) - Column definitions + CREATE TABLE SQL
- **Data export** (`sqlite_export_table`) - Export table rows as JSON
- **Data import** (`sqlite_import_json`) - Import JSON array into a table
- **Transactions** (`sqlite_transaction`) - Atomic multi-statement execution
- Path traversal protection, WAL mode, foreign key enforcement

## Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Installation

```bash
# Clone and install
git clone https://github.com/shz6626/sqlite-mcp-server.git
cd sqlite-mcp-server
uv sync
```

### Run

```bash
uv run sqlite-mcp-server --db mydatabase.db
```

Or via environment variable:

```bash
SQLITE_DB_PATH=mydatabase.db uv run sqlite-mcp-server
```

The server communicates via stdio (MCP protocol). Connect it to any MCP-compatible AI client.

### OpenCode Configuration

Add to `~/.config/opencode/opencode.json`:

```json
{
  "mcp": {
    "sqlite": {
      "type": "local",
      "command": ["uv", "run", "--directory", "/path/to/sqlite-mcp-server", "sqlite-mcp-server"],
      "enabled": true
    }
  }
}
```

## Tools Reference

| Tool | Parameters | Description |
|------|-----------|-------------|
| `sqlite_query` | `sql` (str), `db_path?` (str) | Run read-only SELECT query |
| `sqlite_execute` | `sql` (str), `db_path?` (str) | Run INSERT/UPDATE/DELETE/DDL |
| `sqlite_list_tables` | `db_path?` (str) | List all tables |
| `sqlite_describe_table` | `table` (str), `db_path?` (str) | Show table schema |
| `sqlite_export_table` | `table` (str), `db_path?`, `limit?` (int) | Export rows as JSON |
| `sqlite_import_json` | `table` (str), `data` (str), `db_path?` | Import JSON into table |
| `sqlite_transaction` | `statements` (list[str]), `db_path?` | Atomic multi-statement txns |

All tools accept optional `db_path` (default: `database.db`). Paths resolve relative to the AI client's working directory.

## Security

- Path traversal blocked (`..` rejected)
- Read-only connections for query operations
- Write operations require explicit tool calls
- All SQL executed via parameterized statements where possible

## License

MIT
