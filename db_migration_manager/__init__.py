"""
Database Migration Manager

A comprehensive, ORM-agnostic database migration system with FastAPI integration,
supporting PostgreSQL, MySQL, and SQLite databases.
"""

__version__ = "2.0.0"
__author__ = "Ari Munandar"
__email__ = "arimunandar.dev@gmail.com"

# Core exports
from .core.migration import Migration
from .core.manager import MigrationManager
from .core.models import MigrationRecord, MigrationStatus

# Pydantic support
from .core.pydantic_migration import (
    PydanticMigration,
    DatabaseModel,
    create_migration_from_models,
)
from .core.schema import (
    PydanticSchemaGenerator,
    SchemaComparator,
    TableDefinition,
    ColumnDefinition,
    IndexDefinition,
    ConstraintDefinition,
    db_field,
    primary_key,
    unique_field,
    indexed_field,
)

# Database adapters
from .adapters.sqlite import SQLiteAdapter
from .adapters.postgresql import PostgreSQLAdapter
from .adapters.mysql import MySQLAdapter

__all__ = [
    # Core migration classes
    "Migration",
    "MigrationManager", 
    "MigrationRecord",
    "MigrationStatus",
    
    # Pydantic support
    "PydanticMigration",
    "DatabaseModel",
    "create_migration_from_models",
    "PydanticSchemaGenerator",
    "SchemaComparator",
    "TableDefinition",
    "ColumnDefinition", 
    "IndexDefinition",
    "ConstraintDefinition",
    "db_field",
    "primary_key",
    "unique_field",
    "indexed_field",
    
    # Database adapters
    "SQLiteAdapter",
    "PostgreSQLAdapter",
    "MySQLAdapter",
]