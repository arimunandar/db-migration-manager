"""
PostgreSQL database adapter
"""

from typing import Dict, List, Optional, Any
from .base import DatabaseAdapter


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter with parameterized queries"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._connection = None
        self._transaction = None
    
    async def _get_connection(self):
        """Get or create database connection"""
        if not self._connection:
            try:
                import asyncpg
            except ImportError:
                raise ImportError(
                    "asyncpg is required for PostgreSQL adapter. "
                    "Install with: pip install asyncpg"
                )
            self._connection = await asyncpg.connect(self.connection_string)
        return self._connection
    
    def format_placeholder(self, index: int) -> str:
        """Format parameter placeholder for PostgreSQL"""
        return f"${index}"
    
    async def execute_sql(self, sql: str, params: Optional[tuple] = None) -> Any:
        """Execute SQL statement with parameters"""
        conn = await self._get_connection()
        if params:
            return await conn.execute(sql, *params)
        else:
            return await conn.execute(sql)
    
    async def fetch_all(self, sql: str, params: Optional[tuple] = None) -> List[Dict]:
        """Fetch all results from SQL query"""
        conn = await self._get_connection()
        if params:
            rows = await conn.fetch(sql, *params)
        else:
            rows = await conn.fetch(sql)
        return [dict(row) for row in rows]
    
    async def fetch_one(self, sql: str, params: Optional[tuple] = None) -> Optional[Dict]:
        """Fetch one result from SQL query"""
        conn = await self._get_connection()
        if params:
            row = await conn.fetchrow(sql, *params)
        else:
            row = await conn.fetchrow(sql)
        return dict(row) if row else None
    
    async def begin_transaction(self):
        """Begin database transaction"""
        conn = await self._get_connection()
        self._transaction = conn.transaction()
        await self._transaction.start()
    
    async def commit_transaction(self):
        """Commit database transaction"""
        if self._transaction:
            await self._transaction.commit()
            self._transaction = None
    
    async def rollback_transaction(self):
        """Rollback database transaction"""
        if self._transaction:
            await self._transaction.rollback()
            self._transaction = None
    
    async def get_table_schema(self, table_name: str) -> Dict:
        """Get table schema information"""
        sql = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = $1 AND table_schema = 'public'
        ORDER BY ordinal_position
        """
        rows = await self.fetch_all(sql, (table_name,))
        return {
            "table_name": table_name,
            "columns": rows
        }
    
    async def get_all_tables(self) -> List[str]:
        """Get all table names"""
        sql = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        """
        rows = await self.fetch_all(sql)
        return [row["table_name"] for row in rows]
    
    async def close(self):
        """Close database connection"""
        if self._transaction:
            await self.rollback_transaction()
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    def get_migration_table_sql(self) -> str:
        """Get SQL for creating migration history table (PostgreSQL specific)"""
        return """
        CREATE TABLE IF NOT EXISTS migration_history (
            version VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) NOT NULL,
            checksum VARCHAR(32) NOT NULL,
            execution_time FLOAT NOT NULL,
            rollback_sql TEXT,
            error_message TEXT
        )
        """