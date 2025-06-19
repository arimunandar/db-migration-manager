# DB Migration Manager

A comprehensive, ORM-agnostic database migration system with FastAPI integration and **Pydantic model support**, supporting PostgreSQL, MySQL, and SQLite.

[![PyPI version](https://badge.fury.io/py/db-migration-manager.svg)](https://badge.fury.io/py/db-migration-manager)
[![Python Support](https://img.shields.io/pypi/pyversions/db-migration-manager.svg)](https://pypi.org/project/db-migration-manager/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🚀 **Version Control**: Track and apply database schema changes systematically
- 🔄 **Auto-diff**: Generate migrations automatically from schema differences  
- ✨ **Pydantic Support**: Create migrations directly from Pydantic models
- ⏪ **Rollback Support**: Safely rollback migrations when needed
- 🌐 **FastAPI Integration**: REST API for migration management
- 🐳 **Docker Support**: Easy setup with Docker Compose
- 🗄️ **Multiple Database Support**: PostgreSQL, MySQL, SQLite adapters
- 🔒 **Security**: Parameterized queries prevent SQL injection
- 📝 **Transaction Safety**: Atomic migrations with automatic rollback on failure
- 🎯 **Type Safety**: Full type hints and mypy support
- 🧪 **Testing**: Comprehensive test suite

## Installation

### Basic Installation
```bash
pip install db-migration-manager
```

### With Database-Specific Dependencies
```bash
# PostgreSQL support
pip install db-migration-manager[postgresql]

# MySQL support  
pip install db-migration-manager[mysql]

# SQLite support
pip install db-migration-manager[sqlite]

# FastAPI integration
pip install db-migration-manager[fastapi]

# All dependencies
pip install db-migration-manager[all]
```

## Quick Start

### 1. Basic Usage

```python
import asyncio
from db_migration_manager import PostgreSQLAdapter, MigrationManager

async def main():
    # Initialize database adapter
    db_adapter = PostgreSQLAdapter("postgresql://user:pass@localhost/db")
    
    # Create migration manager
    manager = MigrationManager(db_adapter)
    await manager.initialize()
    
    # Create a migration
    await manager.create_migration(
        "create_users_table",
        up_sql="""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        down_sql="DROP TABLE users"
    )
    
    # Apply migrations
    results = await manager.migrate()
    print(f"Applied {len(results)} migrations")
    
    # Get status
    status = await manager.get_migration_status()
    print(f"Applied: {status['applied_count']}, Pending: {status['pending_count']}")

asyncio.run(main())
```

### 2. Pydantic Model Support

Define your database schema using Pydantic models:

```python
from datetime import datetime
from typing import Optional
from pydantic import Field
from db_migration_manager import DatabaseModel, primary_key, unique_field, indexed_field

class User(DatabaseModel):
    # Primary key with auto-increment
    id: int = primary_key(default=None)
    
    # Unique email field
    email: str = unique_field(max_length=255)
    
    # Username with unique constraint
    username: str = db_field(unique=True, max_length=50)
    
    # Full name
    full_name: str = Field(..., max_length=255)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True)
    
    class Config:
        __table_name__ = "users"

# Create migration from models
import asyncio
from db_migration_manager import PostgreSQLAdapter, MigrationManager

async def create_migration_from_models():
    db_adapter = PostgreSQLAdapter("postgresql://user:pass@localhost/db")
    manager = MigrationManager(db_adapter)
    await manager.initialize()
    
    # Create migration from Pydantic models
    filepath = await manager.create_migration_from_models(
        name="create_user_table",
        models=[User],
        auto_diff=True  # Automatically compare with previous schema
    )
    
    print(f"Created migration: {filepath}")
    
    # Apply the migration
    results = await manager.migrate()
    print(f"Applied {len(results)} migrations")

asyncio.run(create_migration_from_models())
```

### 3. FastAPI Integration

```python
from fastapi import FastAPI
from db_migration_manager import PostgreSQLAdapter, MigrationManager
from db_migration_manager.api import add_migration_routes

app = FastAPI()

# Initialize migration manager
db_adapter = PostgreSQLAdapter("postgresql://user:pass@localhost/db")
manager = MigrationManager(db_adapter)

# Add migration routes
add_migration_routes(app, manager)

# Your API endpoints...
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Available migration endpoints:
# GET  /health                          - Health check
# GET  /migrations/status               - Migration status
# GET  /migrations/pending              - Pending migrations
# POST /migrations/migrate              - Apply migrations
# POST /migrations/rollback             - Rollback migrations  
# POST /migrations/create               - Create new migration
# POST /migrations/create-from-models   - Create migration from Pydantic models
# POST /migrations/validate-models      - Validate Pydantic models
# POST /migrations/show-sql             - Show SQL for Pydantic model
```

### 4. CLI Usage

```bash
# Set database URL
export DATABASE_URL="postgresql://user:pass@localhost/db"

# Check migration status
db-migrate status

# Create a new migration
db-migrate create add_user_profile --up-sql "ALTER TABLE users ADD COLUMN profile TEXT"

# Apply pending migrations
db-migrate migrate

# Rollback to specific version
db-migrate rollback 20240101_120000

# Create migration from Pydantic models
db-migrate create-from-models create_users my_app.models

# Validate Pydantic models
db-migrate validate-models my_app.models

# Show SQL for a specific model
db-migrate show-sql User my_app.models --dialect postgresql

# Help
db-migrate --help
```

## Database Adapters

### PostgreSQL
```python
from db_migration_manager import PostgreSQLAdapter

adapter = PostgreSQLAdapter("postgresql://user:pass@localhost:5432/dbname")
```

### MySQL
```python
from db_migration_manager import MySQLAdapter

adapter = MySQLAdapter({
    'host': 'localhost',
    'user': 'user',
    'password': 'password',
    'db': 'dbname',
    'port': 3306
})
```

### SQLite
```python
from db_migration_manager import SQLiteAdapter

adapter = SQLiteAdapter("path/to/database.db")
```

## Pydantic Model Annotations

The library provides special field annotations for database-specific features:

```python
from db_migration_manager import (
    DatabaseModel, 
    primary_key, 
    unique_field, 
    indexed_field, 
    db_field
)

class User(DatabaseModel):
    # Primary key with auto-increment
    id: int = primary_key(default=None)
    
    # Unique field with length constraint
    email: str = unique_field(max_length=255)
    
    # Indexed field
    username: str = indexed_field(max_length=50)
    
    # Custom field with multiple constraints
    slug: str = db_field(
        unique=True, 
        index=True, 
        max_length=100
    )
    
    # Regular Pydantic field (stored as TEXT/VARCHAR)
    bio: Optional[str] = None
    
    # JSON field (stored as JSONB in PostgreSQL, JSON in MySQL, TEXT in SQLite)
    metadata: dict = Field(default_factory=dict)
    
    # Enum field (stored as VARCHAR)
    status: UserStatus = Field(default=UserStatus.ACTIVE)
```

### Supported Field Annotations

- `primary_key(**kwargs)` - Creates a primary key field with auto-increment
- `unique_field(**kwargs)` - Creates a unique field
- `indexed_field(**kwargs)` - Creates an indexed field  
- `db_field(**kwargs)` - Custom field with database-specific options:
  - `primary_key: bool` - Primary key constraint
  - `unique: bool` - Unique constraint
  - `index: bool` - Create index
  - `unique_index: bool` - Create unique index
  - `auto_increment: bool` - Auto-increment for integers
  - `max_length: int` - Maximum length for strings

### Type Mapping

| Python Type | PostgreSQL | MySQL | SQLite |
|-------------|------------|--------|--------|
| `str` | VARCHAR(255) | VARCHAR(255) | TEXT |
| `int` | INTEGER | INT | INTEGER |
| `float` | DOUBLE PRECISION | DOUBLE | REAL |
| `bool` | BOOLEAN | TINYINT(1) | INTEGER |
| `datetime` | TIMESTAMP | DATETIME | TIMESTAMP |
| `date` | DATE | DATE | DATE |
| `Decimal` | DECIMAL | DECIMAL | DECIMAL |
| `list`/`dict` | JSONB | JSON | TEXT |
| `Enum` | VARCHAR(50) | VARCHAR(50) | TEXT |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](https://github.com/arimunandar/db-migration-manager#readme)
- 🐛 [Issue Tracker](https://github.com/arimunandar/db-migration-manager/issues)
- 💬 [Discussions](https://github.com/arimunandar/db-migration-manager/discussions)

## Related Projects

- [Alembic](https://alembic.sqlalchemy.org/) - SQLAlchemy-based migrations
- [Django Migrations](https://docs.djangoproject.com/en/stable/topics/migrations/) - Django's migration system
- [Flyway](https://flywaydb.org/) - Database migration tool for Java