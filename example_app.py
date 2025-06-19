"""
Example FastAPI application using db-migration-manager
"""

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from db_migration_manager import PostgreSQLAdapter, MigrationManager
from db_migration_manager.api import add_migration_routes


# Global migration manager
migration_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global migration_manager
    
    # Startup
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/migration_demo")
    
    try:
        # Initialize migration system
        db_adapter = PostgreSQLAdapter(database_url)
        migration_manager = MigrationManager(db_adapter, "example_migrations")
        await migration_manager.initialize()
        
        # Create some example migrations if they don't exist
        await create_example_migrations(migration_manager)
        
        print("✅ Migration system initialized")
        yield
        
    except Exception as e:
        print(f"❌ Failed to initialize migration system: {e}")
        yield
    finally:
        # Shutdown
        if migration_manager:
            await migration_manager.close()
            print("🔒 Database connection closed")


async def create_example_migrations(manager: MigrationManager):
    """Create example migrations for demonstration"""
    
    # Check if migrations already exist
    status = await manager.get_migration_status()
    if status['applied_count'] > 0 or status['pending_count'] > 0:
        print("📋 Using existing migrations")
        return
    
    # Create example migrations
    print("📝 Creating example migrations...")
    
    # Users table
    await manager.create_migration(
        "create_users_table",
        up_sql=\"\"\"
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_users_email ON users(email);
        \"\"\",
        down_sql="DROP TABLE IF EXISTS users CASCADE;"
    )
    
    await asyncio.sleep(1)  # Ensure different timestamps
    
    # Posts table
    await manager.create_migration(
        "create_posts_table",
        up_sql=\"\"\"
        CREATE TABLE posts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            content TEXT,
            published BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_posts_user_id ON posts(user_id);
        CREATE INDEX idx_posts_published ON posts(published);
        \"\"\",
        down_sql="DROP TABLE IF EXISTS posts CASCADE;"
    )
    
    await asyncio.sleep(1)  # Ensure different timestamps
    
    # Add profile column
    await manager.create_migration(
        "add_user_profile",
        up_sql=\"\"\"
        ALTER TABLE users 
        ADD COLUMN profile_image VARCHAR(255),
        ADD COLUMN bio TEXT;
        \"\"\",
        down_sql=\"\"\"
        ALTER TABLE users 
        DROP COLUMN IF EXISTS profile_image,
        DROP COLUMN IF EXISTS bio;
        \"\"\"
    )
    
    print("✅ Example migrations created")


# Create FastAPI app
app = FastAPI(
    title="DB Migration Manager Example",
    description="Example application demonstrating db-migration-manager",
    version="1.0.0",
    lifespan=lifespan
)

# Add migration routes
add_migration_routes(app, migration_manager)


@app.get("/", response_class=HTMLResponse)
async def root():
    \"\"\"Welcome page with migration management interface\"\"\"
    return \"\"\"
    <!DOCTYPE html>
    <html>
    <head>
        <title>DB Migration Manager Example</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; }
            .endpoint { 
                background: #f5f5f5; 
                padding: 10px; 
                margin: 10px 0; 
                border-radius: 5px; 
            }
            .method { 
                font-weight: bold; 
                color: white; 
                padding: 3px 8px; 
                border-radius: 3px; 
                margin-right: 10px;
            }
            .get { background: #28a745; }
            .post { background: #007bff; }
            code { background: #e9ecef; padding: 2px 4px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🗄️ DB Migration Manager Example</h1>
            <p>This example demonstrates the db-migration-manager package with FastAPI integration.</p>
            
            <h2>Available Endpoints</h2>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <a href="/health">/health</a> - Health check
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <a href="/migrations/status">/migrations/status</a> - Get migration status
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <a href="/migrations/pending">/migrations/pending</a> - Get pending migrations
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/migrations/migrate</code> - Apply migrations
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/migrations/rollback</code> - Rollback migrations
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <code>/migrations/create</code> - Create new migration
            </div>
            
            <h2>Getting Started</h2>
            <ol>
                <li>Set up PostgreSQL database</li>
                <li>Set DATABASE_URL environment variable</li>
                <li>Run: <code>uvicorn example_app:app --reload</code></li>
                <li>Visit the migration endpoints above</li>
            </ol>
        </div>
    </body>
    </html>
    \"\"\"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)