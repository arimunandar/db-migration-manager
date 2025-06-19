"""
Example FastAPI application demonstrating the migration system
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from db_migration_manager import (
    MigrationManager,
    SQLiteAdapter,
    PostgreSQLAdapter,
    add_migration_routes
)


# Global migration manager
migration_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global migration_manager
    
    # Startup
    database_url = os.getenv("DATABASE_URL", "sqlite://example.db")
    
    if database_url.startswith("sqlite://"):
        db_path = database_url.replace("sqlite://", "")
        db_adapter = SQLiteAdapter(db_path)
    elif database_url.startswith(("postgresql://", "postgres://")):
        db_adapter = PostgreSQLAdapter(database_url)
    else:
        raise ValueError(f"Unsupported database URL: {database_url}")
    
    migration_manager = MigrationManager(db_adapter, "migrations")
    await migration_manager.initialize()
    
    yield
    
    # Shutdown
    if migration_manager:
        await migration_manager.close()


# Create FastAPI app
app = FastAPI(
    title="Database Migration Manager",
    description="Example application with database migration system",
    version="1.1.0",
    lifespan=lifespan
)


# Add migration routes
add_migration_routes(app, lambda: migration_manager)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Database Migration Manager Example",
        "version": "1.1.0",
        "endpoints": {
            "status": "/migrations/status",
            "migrate": "/migrations/migrate",
            "rollback": "/migrations/rollback",
            "create": "/migrations/create",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.post("/demo/setup")
async def demo_setup():
    """Set up demo migrations for testing"""
    try:
        # Create example migrations
        migration1 = await migration_manager.create_migration(
            "create_users_table",
            up_sql="""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            down_sql="DROP TABLE users"
        )
        
        migration2 = await migration_manager.create_migration(
            "add_user_profile",
            up_sql="""
            CREATE TABLE user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                bio TEXT,
                avatar_url TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """,
            down_sql="DROP TABLE user_profiles"
        )
        
        # Apply migrations
        results = await migration_manager.migrate()
        
        return {
            "success": True,
            "message": "Demo setup completed",
            "data": {
                "created_migrations": [migration1, migration2],
                "applied_count": len(results),
                "results": [r.to_dict() for r in results]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/reset")
async def demo_reset():
    """Reset demo by rolling back all migrations"""
    try:
        # Get all applied migrations and rollback to beginning
        status = await migration_manager.get_migration_status()
        
        if status["applied_count"] == 0:
            return {"message": "No migrations to rollback"}
        
        # Rollback all migrations by using a very early timestamp
        results = await migration_manager.rollback("19700101_000000")
        
        return {
            "success": True,
            "message": "Demo reset completed",
            "data": {
                "rolled_back_count": len(results),
                "results": [r.to_dict() for r in results]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "example_app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )