"""
SQLite database adapter
"""

from typing import Dict, List, Optional, Any
from .base import DatabaseAdapter


class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self._connection = None
    
    async def _get_connection(self):
        """Get or create database connection"""
        if not self._connection:
            try:
                import aiosqlite
            except ImportError:
                raise ImportError(
                    "aiosqlite is required for SQLite adapter. "
                    "Install with: pip install aiosqlite"
                )
            self._connection = await aiosqlite.connect(self.database_path)
        return self._connection
    
    def format_placeholder(self, index: int) -> str:
        """Format parameter placeholder for SQLite"""
        return "?"
    
    async def execute_sql(self, sql: str, params: Optional[tuple] = None) -> Any:
        """Execute SQL statement with parameters"""
        conn = await self._get_connection()
        cursor = await conn.execute(sql, params or ())
        await conn.commit()
        return cursor.rowcount
    
    async def fetch_all(self, sql: str, params: Optional[tuple] = None) -> List[Dict]:
        """Fetch all results from SQL query"""
        conn = await self._get_connection()
        cursor = await conn.execute(sql, params or ())
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    
    async def fetch_one(self, sql: str, params: Optional[tuple] = None) -> Optional[Dict]:
        """Fetch one result from SQL query"""
        conn = await self._get_connection()
        cursor = await conn.execute(sql, params or ())
        row = await cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None
    
    async def begin_transaction(self):
        """Begin database transaction"""
        conn = await self._get_connection()
        await conn.execute("BEGIN")
    
    async def commit_transaction(self):
        """Commit database transaction"""
        conn = await self._get_connection()
        await conn.commit()
    
    async def rollback_transaction(self):
        """Rollback database transaction"""
        conn = await self._get_connection()
        await conn.rollback()
    
    async def get_table_schema(self, table_name: str) -> Dict:
        """Get table schema information"""
        sql = f"PRAGMA table_info({table_name})"
        rows = await self.fetch_all(sql)
        return {
            "table_name": table_name,
            "columns": [
                {
                    "column_name": row["name"],
                    "data_type": row["type"],
                    "is_nullable": "YES" if not row["notnull"] else "NO",
                    "column_default": row["dflt_value"]
                }
                for row in rows
            ]
        }
    
    async def get_all_tables(self) -> List[str]:
        """Get all table names"""
        sql = "SELECT name FROM sqlite_master WHERE type='table'"
        rows = await self.fetch_all(sql)
        return [
            row["name"] for row in rows 
            if row["name"] not in ("sqlite_sequence", "migration_history")
        ]
    
    async def close(self):
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    def get_migration_table_sql(self) -> str:
        """Get SQL for creating migration history table (SQLite specific)"""
        return """
        CREATE TABLE IF NOT EXISTS migration_history (
            version TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL,
            checksum TEXT NOT NULL,
            execution_time REAL NOT NULL,
            rollback_sql TEXT,
            error_message TEXT
        )
        """