"""
Abstract base class for database adapters
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters"""
    
    @abstractmethod
    async def execute_sql(self, sql: str, params: Optional[tuple] = None) -> Any:
        """Execute SQL statement with optional parameters"""
        pass
    
    @abstractmethod
    async def fetch_all(self, sql: str, params: Optional[tuple] = None) -> List[Dict]:
        """Fetch all results from SQL query with optional parameters"""
        pass
    
    @abstractmethod
    async def fetch_one(self, sql: str, params: Optional[tuple] = None) -> Optional[Dict]:
        """Fetch one result from SQL query with optional parameters"""
        pass
    
    @abstractmethod
    async def begin_transaction(self):
        """Begin database transaction"""
        pass
    
    @abstractmethod
    async def commit_transaction(self):
        """Commit database transaction"""
        pass
    
    @abstractmethod
    async def rollback_transaction(self):
        """Rollback database transaction"""
        pass
    
    @abstractmethod
    async def get_table_schema(self, table_name: str) -> Dict:
        """Get table schema information"""
        pass
    
    @abstractmethod
    async def get_all_tables(self) -> List[str]:
        """Get all table names"""
        pass
    
    @abstractmethod
    async def close(self):
        """Close database connection"""
        pass
    
    # Common utility methods that can be overridden
    def format_placeholder(self, index: int) -> str:
        """Format parameter placeholder for the database"""
        return "?"
    
    def get_migration_table_sql(self) -> str:
        """Get SQL for creating migration history table"""
        return """
        CREATE TABLE IF NOT EXISTS migration_history (
            version VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            applied_at TIMESTAMP NOT NULL,
            status VARCHAR(50) NOT NULL,
            checksum VARCHAR(32) NOT NULL,
            execution_time FLOAT NOT NULL,
            rollback_sql TEXT,
            error_message TEXT
        )
        """