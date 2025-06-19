"""
FastAPI routes for migration management
"""

from typing import Optional, List, Type
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..core.manager import MigrationManager
from .models import (
    MigrationResponse, 
    CreateMigrationRequest, 
    MigrateRequest, 
    RollbackRequest,
    CreateFromModelsRequest,
    ValidateModelsRequest,
    ShowSQLRequest
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
    
    @app.post(f"{prefix}/create-from-models", response_model=MigrationResponse)
    async def create_migration_from_models(request: CreateFromModelsRequest):
        """Create a migration from Pydantic models"""
        try:
            # Load models from module
            models = load_models_from_module(request.models_module, request.model_names)
            
            if not models:
                raise HTTPException(
                    status_code=400, 
                    detail="No Pydantic models found in the specified module"
                )
            
            # Validate models first
            validation = migration_manager.validate_models_schema(models)
            
            if validation['errors']:
                return MigrationResponse.error_response(
                    "Model validation failed",
                    data={"validation": validation}
                )
            
            # Create migration
            filepath = await migration_manager.create_migration_from_models(
                name=request.name,
                models=models,
                auto_diff=request.auto_diff
            )
            
            return MigrationResponse.success_response(
                f"Created migration from {len(models)} models",
                data={
                    "filepath": filepath,
                    "models": [{"name": m.__name__, "table": getattr(m, '__table_name__', m.__name__.lower())} for m in models],
                    "validation": validation
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post(f"{prefix}/validate-models", response_model=MigrationResponse)
    async def validate_pydantic_models(request: ValidateModelsRequest):
        """Validate Pydantic models for database compatibility"""
        try:
            # Load models from module
            models = load_models_from_module(request.models_module, request.model_names)
            
            if not models:
                raise HTTPException(
                    status_code=400, 
                    detail="No Pydantic models found in the specified module"
                )
            
            validation = migration_manager.validate_models_schema(models)
            
            success = len(validation['errors']) == 0
            message = f"Validated {len(models)} models"
            if validation['errors']:
                message += f" with {len(validation['errors'])} errors"
            if validation['warnings']:
                message += f" and {len(validation['warnings'])} warnings"
            
            return MigrationResponse(
                success=success,
                message=message,
                data={
                    "models": [{"name": m.__name__, "table": getattr(m, '__table_name__', m.__name__.lower())} for m in models],
                    "validation": validation
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post(f"{prefix}/show-sql", response_model=MigrationResponse)
    async def show_model_sql(request: ShowSQLRequest):
        """Show SQL that would be generated for a Pydantic model"""
        try:
            # Load specific model
            models = load_models_from_module(request.models_module, [request.model_class])
            
            if not models:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Model '{request.model_class}' not found in module '{request.models_module}'"
                )
            
            model = models[0]
            
            # Generate SQL
            create_sql = model.generate_table_sql(request.dialect)
            drop_sql = model.generate_drop_sql(request.dialect)
            
            return MigrationResponse.success_response(
                f"Generated SQL for model '{model.__name__}'",
                data={
                    "model": model.__name__,
                    "table_name": getattr(model, '__table_name__', model.__name__.lower()),
                    "dialect": request.dialect,
                    "create_sql": create_sql,
                    "drop_sql": drop_sql
                }
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


def load_models_from_module(module_path: str, model_names: Optional[List[str]] = None) -> List[Type[BaseModel]]:
    """Load Pydantic models from a Python module - API version"""
    import importlib
    import sys
    from pathlib import Path
    
    try:
        # Add current directory to Python path if not already there
        current_dir = str(Path.cwd())
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Import the module
        module = importlib.import_module(module_path)
        
        # Find Pydantic models in the module
        models = []
        for attr_name in dir(module):
            if model_names and attr_name not in model_names:
                continue
                
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, BaseModel) and 
                attr != BaseModel):
                models.append(attr)
        
        return models
        
    except Exception as e:
        raise ImportError(f"Failed to load models from '{module_path}': {e}")