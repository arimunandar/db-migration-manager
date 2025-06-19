"""
CLI commands for migration management
"""

import asyncio
import importlib.util
import os
import sys
from pathlib import Path
from typing import Optional, List, Type

import click
from pydantic import BaseModel

from ..adapters.postgresql import PostgreSQLAdapter
from ..adapters.mysql import MySQLAdapter
from ..adapters.sqlite import SQLiteAdapter
from ..core.manager import MigrationManager


def get_db_adapter(database_url: str):
    """Get database adapter based on URL"""
    if database_url.startswith("postgresql://") or database_url.startswith("postgres://"):
        return PostgreSQLAdapter(database_url)
    elif database_url.startswith("mysql://"):
        # Convert to connection config for MySQL
        # This is a simplified version - in practice you'd parse the URL properly
        raise NotImplementedError("MySQL URL parsing not implemented in CLI")
    elif database_url.startswith("sqlite://"):
        db_path = database_url.replace("sqlite://", "")
        return SQLiteAdapter(db_path)
    else:
        raise ValueError(f"Unsupported database URL: {database_url}")


@click.group()
@click.option('--database-url', envvar='DATABASE_URL', 
              help='Database connection URL (can also use DATABASE_URL env var)')
@click.option('--migrations-dir', default='migrations',
              help='Migrations directory (default: migrations)')
@click.pass_context
def cli(ctx, database_url: Optional[str], migrations_dir: str):
    """Database Migration Manager CLI"""
    ctx.ensure_object(dict)
    ctx.obj['database_url'] = database_url
    ctx.obj['migrations_dir'] = migrations_dir


async def get_migration_manager(ctx):
    """Helper to create and initialize migration manager"""
    database_url = ctx.obj['database_url']
    migrations_dir = ctx.obj['migrations_dir']
    
    if not database_url:
        raise ValueError("DATABASE_URL is required")
    
    db_adapter = get_db_adapter(database_url)
    manager = MigrationManager(db_adapter, migrations_dir)
    await manager.initialize()
    return manager


@cli.command()
@click.pass_context
def status(ctx):
    """Show migration status"""
    async def async_status():
        manager = None
        try:
            manager = await get_migration_manager(ctx)
            status = await manager.get_migration_status()
            
            click.echo("Migration Status:")
            click.echo(f"Applied migrations: {status['applied_count']}")
            click.echo(f"Pending migrations: {status['pending_count']}")
            
            if status.get('last_applied'):
                click.echo(f"Last applied: {status['last_applied']}")
            
            if status.get('next_pending'):
                click.echo(f"Next pending: {status['next_pending']}")
            
            if status['pending_count'] > 0:
                click.echo("\nPending migrations:")
                for migration in status['pending_migrations']:
                    click.echo(f"  - {migration['version']}: {migration['name']}")
            
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            ctx.exit(1)
        finally:
            if manager:
                await manager.close()
    
    asyncio.run(async_status())


@cli.command()
@click.option('--target', help='Target version to migrate to')
@click.pass_context
def migrate(ctx, target: Optional[str]):
    """Apply pending migrations"""
    async def async_migrate():
        manager = None
        try:
            manager = await get_migration_manager(ctx)
            results = await manager.migrate(target)
            
            if not results:
                click.echo("No pending migrations to apply")
                return
            
            for result in results:
                status_color = 'green' if result.status.value == 'applied' else 'red'
                click.echo(f"Migration {result.version}: ", nl=False)
                click.secho(result.status.value.upper(), fg=status_color)
                
                if result.error_message:
                    click.echo(f"  Error: {result.error_message}")
            
            success_count = sum(1 for r in results if r.status.value == 'applied')
            click.echo(f"\nApplied {success_count}/{len(results)} migrations successfully")
            
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            ctx.exit(1)
        finally:
            if manager:
                await manager.close()
    
    asyncio.run(async_migrate())


@cli.command()
@click.argument('target_version')
@click.pass_context
def rollback(ctx, target_version: str):
    """Rollback migrations to target version"""
    async def async_rollback():
        manager = None
        try:
            manager = await get_migration_manager(ctx)
            results = await manager.rollback(target_version)
            
            if not results:
                click.echo("No migrations to rollback")
                return
            
            for result in results:
                status_color = 'green' if result.status.value == 'rolled_back' else 'red'
                click.echo(f"Migration {result.version}: ", nl=False)
                click.secho(result.status.value.upper(), fg=status_color)
                
                if result.error_message:
                    click.echo(f"  Error: {result.error_message}")
            
            success_count = sum(1 for r in results if r.status.value == 'rolled_back')
            click.echo(f"\nRolled back {success_count}/{len(results)} migrations successfully")
            
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            ctx.exit(1)
        finally:
            if manager:
                await manager.close()
    
    asyncio.run(async_rollback())


@cli.command()
@click.argument('name')
@click.option('--up-sql', default='', help='SQL for applying the migration')
@click.option('--down-sql', default='', help='SQL for rolling back the migration')
@click.pass_context
def create(ctx, name: str, up_sql: str, down_sql: str):
    """Create a new migration file"""
    async def async_create():
        manager = None
        try:
            manager = await get_migration_manager(ctx)
            filepath = await manager.create_migration(name, up_sql, down_sql)
            click.echo(f"Created migration: {filepath}")
            
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            ctx.exit(1)
        finally:
            if manager:
                await manager.close()
    
    asyncio.run(async_create())


@cli.command()
@click.argument('name')
@click.argument('models_module')
@click.option('--models', multiple=True, help='Specific model class names to include')
@click.option('--no-auto-diff', is_flag=True, help='Disable auto-diff with previous snapshot')
@click.pass_context
def create_from_models(ctx, name: str, models_module: str, models: tuple, no_auto_diff: bool):
    """Create a migration from Pydantic models
    
    Examples:
        db-migrate create-from-models create_users app.models
        db-migrate create-from-models add_profile app.models --models User --models Profile
    """
    async def async_create_from_models():
        manager = None
        try:
            # Load the models module
            pydantic_models = load_models_from_module(models_module, list(models) if models else None)
            
            if not pydantic_models:
                click.echo("No Pydantic models found in the specified module")
                ctx.exit(1)
            
            # Validate models first
            manager = await get_migration_manager(ctx)
            validation = manager.validate_models_schema(pydantic_models)
            
            if validation['errors']:
                click.echo("Model validation errors:")
                for error in validation['errors']:
                    click.secho(f"  ❌ {error}", fg='red')
                ctx.exit(1)
            
            if validation['warnings']:
                click.echo("Model validation warnings:")
                for warning in validation['warnings']:
                    click.secho(f"  ⚠️ {warning}", fg='yellow')
            
            # Create migration
            filepath = await manager.create_migration_from_models(
                name=name,
                models=pydantic_models,
                auto_diff=not no_auto_diff
            )
            
            click.echo(f"Created migration from {len(pydantic_models)} models: {filepath}")
            click.echo("Models included:")
            for model in pydantic_models:
                table_name = getattr(model, '__table_name__', model.__name__.lower())
                click.echo(f"  - {model.__name__} -> {table_name}")
            
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            ctx.exit(1)
        finally:
            if manager:
                await manager.close()
    
    asyncio.run(async_create_from_models())


@cli.command()
@click.argument('models_module')
@click.option('--models', multiple=True, help='Specific model class names to validate')
@click.pass_context
def validate_models(ctx, models_module: str, models: tuple):
    """Validate Pydantic models for database compatibility"""
    async def async_validate():
        manager = None
        try:
            # Load the models module
            pydantic_models = load_models_from_module(models_module, list(models) if models else None)
            
            if not pydantic_models:
                click.echo("No Pydantic models found in the specified module")
                ctx.exit(1)
            
            manager = await get_migration_manager(ctx)
            validation = manager.validate_models_schema(pydantic_models)
            
            click.echo(f"Validation results for {len(pydantic_models)} models:")
            
            if validation['errors']:
                click.echo("\n❌ Errors:")
                for error in validation['errors']:
                    click.secho(f"  {error}", fg='red')
            
            if validation['warnings']:
                click.echo("\n⚠️ Warnings:")
                for warning in validation['warnings']:
                    click.secho(f"  {warning}", fg='yellow')
            
            if validation['info']:
                click.echo("\n✅ Validated models:")
                for info in validation['info']:
                    click.secho(f"  {info}", fg='green')
            
            if validation['errors']:
                ctx.exit(1)
            else:
                click.secho("\n✅ All models are valid!", fg='green')
            
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            ctx.exit(1)
        finally:
            if manager:
                await manager.close()
    
    asyncio.run(async_validate())


@cli.command()
@click.argument('model_class')
@click.argument('models_module')
@click.option('--dialect', default='postgresql', type=click.Choice(['postgresql', 'mysql', 'sqlite']),
              help='Database dialect')
@click.pass_context 
def show_sql(ctx, model_class: str, models_module: str, dialect: str):
    """Show the SQL that would be generated for a Pydantic model"""
    try:
        # Load specific model
        models = load_models_from_module(models_module, [model_class])
        
        if not models:
            click.echo(f"Model '{model_class}' not found in module '{models_module}'")
            ctx.exit(1)
        
        model = models[0]
        
        # Generate SQL
        create_sql = model.generate_table_sql(dialect)
        drop_sql = model.generate_drop_sql(dialect)
        
        click.echo(f"SQL for model '{model.__name__}' (dialect: {dialect}):")
        click.echo("\nCREATE TABLE:")
        click.secho(create_sql, fg='green')
        click.echo("\nDROP TABLE:")
        click.secho(drop_sql, fg='red')
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)


def load_models_from_module(module_path: str, model_names: Optional[List[str]] = None) -> List[Type[BaseModel]]:
    """Load Pydantic models from a Python module"""
    try:
        # Add current directory to Python path if not already there
        current_dir = str(Path.cwd())
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Import the module
        if '.' in module_path:
            # Import as package.module
            module = importlib.import_module(module_path)
        else:
            # Import as file path
            module_file = Path(module_path)
            if not module_file.exists():
                module_file = Path(f"{module_path}.py")
            
            if not module_file.exists():
                raise ImportError(f"Module file not found: {module_path}")
            
            spec = importlib.util.spec_from_file_location("models", module_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        
        # Find Pydantic models in the module
        models = []
        for attr_name in dir(module):
            if model_names and attr_name not in model_names:
                continue
                
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, BaseModel) and 
                attr != BaseModel and
                attr.__name__ != 'DatabaseModel' and  # Filter out our base class
                hasattr(attr, 'model_fields') and  # Must have actual fields
                len(attr.model_fields) > 0):  # Must have at least one field
                models.append(attr)
        
        return models
        
    except Exception as e:
        raise ImportError(f"Failed to load models from '{module_path}': {e}")


if __name__ == '__main__':
    cli()