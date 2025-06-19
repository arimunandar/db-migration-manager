# DB Migration Manager

A comprehensive, ORM-agnostic database migration system with FastAPI integration, supporting PostgreSQL, MySQL, and SQLite.

[![PyPI version](https://badge.fury.io/py/db-migration-manager.svg)](https://badge.fury.io/py/db-migration-manager)
[![Python Support](https://img.shields.io/pypi/pyversions/db-migration-manager.svg)](https://pypi.org/project/db-migration-manager/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🚀 **Version Control**: Track and apply database schema changes systematically
- 🔄 **Auto-diff**: Generate migrations automatically from schema differences  
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

### 2. FastAPI Integration

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
# GET  /health                 - Health check
# GET  /migrations/status      - Migration status
# GET  /migrations/pending     - Pending migrations
# POST /migrations/migrate     - Apply migrations
# POST /migrations/rollback    - Rollback migrations  
# POST /migrations/create      - Create new migration
```

### 3. CLI Usage

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