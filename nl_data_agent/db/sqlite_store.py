from __future__ import annotations

import sqlite3
from pathlib import Path

from nl_data_agent.paths import default_db_path


class SqliteStore:
    """Thin SQLite helper for schema introspection and query execution."""

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path else default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection: sqlite3.Connection | None = None
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.execute("PRAGMA foreign_keys = ON")
        except Exception as exc:
            print(f"Error connecting to SQLite database: {exc}")
            self.connection = None

    def schema_context(self) -> str:
        if self.connection is None:
            return "Error: no database connection."

        cursor = self.connection.cursor()
        lines = [f"SQLite database: {self.db_path}", ""]

        try:
            cursor.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
                "ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]

            for table_name in tables:
                lines.append(f"Table: {table_name}")
                cursor.execute(f"PRAGMA table_info({table_name})")
                for col in cursor.fetchall():
                    # cid, name, type, notnull, dflt_value, pk
                    lines.append(f"  Column: {col[1]}, Data Type: {col[2] or 'TEXT'}")

                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                sample_rows = cursor.fetchall()
                lines.append("  Sample Data:")
                for row in sample_rows:
                    lines.append(f"    {row}")
                lines.append("")

            return "\n".join(lines)
        except Exception as exc:
            return f"Error fetching schema details: {exc}"
        finally:
            cursor.close()
            self.close()

    def execute(self, query: str) -> str | None:
        if self.connection is None:
            return None

        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            lowered = query.strip().lower()
            if lowered.startswith("select") or lowered.startswith("with"):
                rows = cursor.fetchall()
                columns = [col[0] for col in (cursor.description or [])]
                self.connection.commit()
                return self._format_rows(columns, rows)
            self.connection.commit()
            return f"Query executed. Rows affected: {cursor.rowcount}"
        except Exception as exc:
            print(f"Error executing query: {exc}")
            return None
        finally:
            if cursor is not None:
                cursor.close()
            self.close()

    @staticmethod
    def _format_rows(columns: list[str], rows: list[tuple]) -> str:
        if not rows:
            return "No rows returned."
        if not columns:
            return "\n".join(str(row) for row in rows)

        header = " | ".join(columns)
        divider = " | ".join("---" for _ in columns)
        body = [" | ".join("" if cell is None else str(cell) for cell in row) for row in rows]
        return "\n".join([header, divider, *body])

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None
