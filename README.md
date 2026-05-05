# sqlite-mcp-server

一个功能完整的 SQLite MCP (Model Context Protocol) 服务器，供 AI 智能体使用。支持查询、执行、DDL、导入导出、事务等。

A full-featured SQLite MCP server for AI agents. Supports query, execute, DDL, import/export, transactions, and more.

---

## 功能 / Features

| 工具 Tool | 功能 Description |
|-----------|-----------------|
| `sqlite_query` | 只读查询 / Read-only SELECT |
| `sqlite_execute` | INSERT / UPDATE / DELETE / DDL（多语句） |
| `sqlite_list_tables` | 列出所有表 / List all tables |
| `sqlite_describe_table` | 查看表结构 + CREATE TABLE SQL / Schema inspection |
| `sqlite_export_table` | 导出表数据为 JSON / Export rows as JSON |
| `sqlite_import_json` | 从 JSON 导入数据 / Import JSON into table |
| `sqlite_transaction` | 原子化多语句执行 / Atomic multi-statement txns |

额外特性 / Extra features：路径遍历防护、WAL 模式、外键约束。

Path traversal protection, WAL journal mode, foreign key enforcement.

---

## 快速开始 / Quick Start

### 环境要求 / Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)（推荐）或 pip

### 安装 / Installation

```bash
git clone https://github.com/shz6626/sqlite-mcp-server.git
cd sqlite-mcp-server
uv sync
```

### 运行 / Run

```bash
uv run sqlite-mcp-server --db mydatabase.db
```

或通过环境变量指定 / Or via environment variable：

```bash
SQLITE_DB_PATH=mydatabase.db uv run sqlite-mcp-server
```

服务器通过 stdio（MCP 协议）通信，可接入任何兼容 MCP 的 AI 客户端。

The server communicates via stdio (MCP protocol). Connect it to any MCP-compatible AI client.

---

## OpenCode 配置 / OpenCode Configuration

在 `~/.config/opencode/opencode.json` 中添加 / Add to `~/.config/opencode/opencode.json`：

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

---

## 工具参数参考 / Tools Reference

所有工具支持可选的 `db_path` 参数（默认 `database.db`），路径相对于 AI 客户端的工作目录。

All tools accept optional `db_path` (default: `database.db`). Paths resolve relative to the AI client's working directory.

| 工具 Tool | 参数 Parameters | 说明 Description |
|-----------|----------------|------------------|
| `sqlite_query` | `sql`, `db_path?` | 执行只读 SELECT / Run read-only SELECT |
| `sqlite_execute` | `sql`, `db_path?` | 执行写入/DDL 语句 / Run write/DDL statements |
| `sqlite_list_tables` | `db_path?` | 列出所有表 / List all tables |
| `sqlite_describe_table` | `table`, `db_path?` | 查看表结构 / Show table schema |
| `sqlite_export_table` | `table`, `db_path?`, `limit?` | 导出为 JSON / Export as JSON |
| `sqlite_import_json` | `table`, `data`, `db_path?` | 从 JSON 导入 / Import from JSON |
| `sqlite_transaction` | `statements[]`, `db_path?` | 原子事务 / Atomic transaction |

---

## 安全 / Security

- 路径遍历已拦截（`..` 被拒绝）/ Path traversal blocked (`..` rejected)
- 查询操作使用只读连接 / Read-only connections for query operations
- 写入操作需显式调用工具 / Write operations require explicit tool calls
- 尽可能使用参数化 SQL / Parameterized SQL where possible

---

## 许可 / License

MIT
