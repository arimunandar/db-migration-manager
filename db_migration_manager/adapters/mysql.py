"""
MySQL database adapter
"""

from typing import Dict, List, Optional, Any
from .base import DatabaseAdapter


class MySQLAdapter(DatabaseAdapter):
    """MySQL database adapter"""
    
    def __init__(self, connection_config: Dict):
        self.connection_config = connection_config
        self._connection = None
        self._transaction_active = False
    
    async def _get_connection(self):
        """Get or create database connection"""
        if not self._connection:
            try:
                import aiomysql
            except ImportError:
                raise ImportError(
                    "aiomysql is required for MySQL adapter. "
                    "Install with: pip install aiomysql"
                )
            self._connection = await aiomysql.connect(**self.connection_config)
        return self._connection
    
    def format_placeholder(self, index: int) -> str:
        """Format parameter placeholder for MySQL"""
        return "%s"
    
    async def execute_sql(self, sql: str, params: Optional[tuple] = None) -> Any:
        """Execute SQL statement with parameters"""
        conn = await self._get_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(sql, params)
            return cursor.rowcount
    
    async def fetch_all(self, sql: str, params: Optional[tuple] = None) -> List[Dict]:
        """Fetch all results from SQL query"""
        try:
            import aiomysql
        except ImportError:
            raise ImportError("aiomysql is required for MySQL adapter")
            
        conn = await self._get_connection()
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(sql, params)
            rows = await cursor.fetchall()
            return list(rows) if rows else []
    
    async def fetch_one(self, sql: str, params: Optional[tuple] = None) -> Optional[Dict]:
        """Fetch one result from SQL query"""
        try:
            import aiomysql
        except ImportError:
            raise ImportError("aiomysql is required for MySQL adapter")
            
        conn = await self._get_connection()
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(sql, params)
            row = await cursor.fetchone()
            return row
    
    async def begin_transaction(self):
        """Begin database transaction"""
        conn = await self._get_connection()
        await conn.begin()
        self._transaction_active = True
    
    async def commit_transaction(self):
        """Commit database transaction"""
        if self._transaction_active:
            conn = await self._get_connection()
            await conn.commit()
            self._transaction_active = False
    
    async def rollback_transaction(self):
        """Rollback database transaction"""
        if self._transaction_active:
            conn = await self._get_connection()
            await conn.rollback()
            self._transaction_active = False
    
    async def get_table_schema(self, table_name: str) -> Dict:
        """Get table schema information"""
        sql = """
        SELECT COLUMN_NAME as column_name, DATA_TYPE as data_type,
               IS_NULLABLE as is_nullable, COLUMN_DEFAULT as column_default
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = %s AND TABLE_SCHEMA = DATABASE()
        ORDER BY ORDINAL_POSITION
        """
        rows = await self.fetch_all(sql, (table_name,))
        return {
            "table_name": table_name,
            "columns": rows
        }
    
    async def get_all_tables(self) -> List[str]:
        """Get all table names"""
        sql = "SHOW TABLES"
        rows = await self.fetch_all(sql)
        return [list(row.values())[0] for row in rows]
    
    async def close(self):
        """Close database connection"""
        if self._transaction_active:
            await self.rollback_transaction()
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def get_migration_table_sql(self) -> str:
        """Get SQL for creating migration history table (MySQL specific)"""
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