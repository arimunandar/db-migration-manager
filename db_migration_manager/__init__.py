"""
DB Migration Manager
===================

A comprehensive, ORM-agnostic database migration system with FastAPI integration.

Features:
- Version Control: Track and apply database schema changes systematically
- Auto-diff: Generate migrations automatically from schema differences
- Rollback Support: Safely rollback migrations when needed
- FastAPI Integration: REST API for migration management
- Docker Support: Easy setup with Docker Compose
- Multiple Database Support: PostgreSQL, MySQL, SQLite adapters

Basic Usage:
-----------

```python
from db_migration_manager import PostgreSQLAdapter, MigrationManager

# Initialize
db_adapter = PostgreSQLAdapter("postgresql://user:pass@localhost/db")
manager = MigrationManager(db_adapter)
await manager.initialize()

# Create migration
await manager.create_migration(
    "create_users_table",
    up_sql="CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(255));",
    down_sql="DROP TABLE users;"
)

# Apply migrations
results = await manager.migrate()
```

FastAPI Integration:
-------------------

```python
from fastapi import FastAPI
from db_migration_manager.api import add_migration_routes

app = FastAPI()
add_migration_routes(app, manager)
```

CLI Usage:
----------

```bash
python -m db_migration_manager.cli status
python -m db_migration_manager.cli migrate
python -m db_migration_manager.cli create my_migration
```
"""

__version__ = "1.0.0"
__author__ = "Ari Munandar"
__email__ = "arimunandar@example.com"
__description__ = "A comprehensive database migration system with FastAPI integration"

# Core exports
from .core.migration import Migration
from .core.manager import MigrationManager
from .core.models import MigrationRecord, MigrationStatus

# Database adapters
from .adapters.postgresql import PostgreSQLAdapter
from .adapters.mysql import MySQLAdapter
from .adapters.sqlite import SQLiteAdapter
from .adapters.base import DatabaseAdapter

# API integration
from .api.routes import add_migration_routes
from .api.models import MigrationResponse

__all__ = [
    # Core
    "Migration",
    "MigrationManager", 
    "MigrationRecord",
    "MigrationStatus",
    
    # Adapters
    "DatabaseAdapter",
    "PostgreSQLAdapter",
    "MySQLAdapter", 
    "SQLiteAdapter",
    
    # API
    "add_migration_routes",
    "MigrationResponse",
    
    # Package info
    "__version__",
    "__author__",
    "__email__",
    "__description__"
]