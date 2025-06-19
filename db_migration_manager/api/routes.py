"""
FastAPI routes for migration management
"""

from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..core.manager import MigrationManager
from .models import (
    MigrationResponse, 
    CreateMigrationRequest, 
    MigrateRequest, 
    RollbackRequest
)


def add_migration_routes(app: FastAPI, migration_manager: MigrationManager, prefix: str = "/migrations"):
    """Add migration routes to FastAPI app"""
    
    @app.get(f"{prefix}/status", response_model=MigrationResponse)
    async def get_migration_status():
        """Get current migration status"""
        try:
            status = await migration_manager.get_migration_status()
            return MigrationResponse.success_response(
                "Migration status retrieved successfully",
                data=status
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get(f"{prefix}/pending", response_model=MigrationResponse)
    async def get_pending_migrations():
        """Get list of pending migrations"""
        try:
            pending = await migration_manager.get_pending_migrations()
            data = {
                "pending_migrations": [
                    {"version": m.version, "name": m.name, "checksum": m.get_checksum()}
                    for m in pending
                ]
            }
            return MigrationResponse.success_response(
                f"Found {len(pending)} pending migrations",
                data=data
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post(f"{prefix}/migrate", response_model=MigrationResponse)
    async def run_migrations(request: MigrateRequest):
        """Run pending migrations"""
        try:
            results = await migration_manager.migrate(request.target_version)
            
            # Convert results to serializable format
            serialized_results = []
            for result in results:
                serialized_results.append(result.to_dict())
            
            success_count = sum(1 for r in results if r.status.value == "applied")
            message = f"Applied {success_count}/{len(results)} migrations successfully"
            
            return MigrationResponse.success_response(
                message,
                data={"results": serialized_results}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post(f"{prefix}/rollback", response_model=MigrationResponse)
    async def rollback_migrations(request: RollbackRequest):
        """Rollback migrations to target version"""
        try:
            results = await migration_manager.rollback(request.target_version)
            
            # Convert results to serializable format
            serialized_results = []
            for result in results:
                serialized_results.append(result.to_dict())
            
            success_count = sum(1 for r in results if r.status.value == "rolled_back")
            message = f"Rolled back {success_count}/{len(results)} migrations successfully"
            
            return MigrationResponse.success_response(
                message,
                data={"results": serialized_results}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post(f"{prefix}/create", response_model=MigrationResponse)
    async def create_migration(request: CreateMigrationRequest):
        """Create a new migration file"""
        try:
            filepath = await migration_manager.create_migration(
                request.name, 
                request.up_sql, 
                request.down_sql
            )
            return MigrationResponse.success_response(
                "Migration created successfully",
                data={"filepath": filepath}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        try:
            # Test database connection
            await migration_manager.db_adapter.fetch_one("SELECT 1")
            return {"status": "healthy", "database": "connected"}
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
            )