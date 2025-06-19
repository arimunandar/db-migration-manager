"""
CLI commands for migration management
"""

import asyncio
import os
from typing import Optional

import click

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


if __name__ == '__main__':
    cli()