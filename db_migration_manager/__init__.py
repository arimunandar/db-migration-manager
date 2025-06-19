"""
Database Migration Manager

A comprehensive, ORM-agnostic database migration system with FastAPI integration,
supporting PostgreSQL, MySQL, and SQLite databases.
"""

__version__ = "1.1.0"
__author__ = "Ari Munandar"
__email__ = "arimunandar.dev@gmail.com"

# Core exports
from .core.migration import Migration
from .core.manager import MigrationManager
from .core.models import MigrationRecord, MigrationStatus

# Database adapters
from .adapters.sqlite import SQLiteAdapter
from .adapters.postgresql import PostgreSQLAdapter
from .adapters.mysql import MySQLAdapter

__all__ = [
    "Migration",
    "MigrationManager",
    "MigrationRecord",
    "MigrationStatus",
    "SQLiteAdapter",
    "PostgreSQLAdapter",
    "MySQLAdapter",
]