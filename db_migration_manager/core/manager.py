"""
Main migration manager with enhanced security
"""

import re
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..adapters.base import DatabaseAdapter
from .migration import Migration
from .models import MigrationRecord, MigrationStatus


class MigrationManager:
    """Main migration manager with security enhancements"""
    
    def __init__(self, db_adapter: DatabaseAdapter, migrations_dir: str = "migrations"):
        self.db_adapter = db_adapter
        self.migrations_dir = Path(migrations_dir)
        self.migrations_dir.mkdir(exist_ok=True)
    
    async def initialize(self):
        """Initialize migration system"""
        await self._create_migration_table()
    
    async def _create_migration_table(self):
        """Create migration history table"""
        create_sql = self.db_adapter.get_migration_table_sql()
        await self.db_adapter.execute_sql(create_sql)
    
    async def create_migration(self, name: str, up_sql: str = "", down_sql: str = "") -> str:
        """Create a new migration file"""
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{version}_{name}.py"
        filepath = self.migrations_dir / filename
        
        migration_content = f'''"""\nMigration: {name}\nCreated: {datetime.now().isoformat()}\n"""\n\nfrom db_migration_manager import Migration\n\nclass {self._to_class_name(name)}(Migration):\n    def __init__(self):\n        super().__init__("{version}", "{name}")\n        self.up_sql = """{up_sql}"""\n        self.down_sql = """{down_sql}"""\n'''
        
        with open(filepath, 'w') as f:
            f.write(migration_content)
        
        return str(filepath)
    
    def _to_class_name(self, name: str) -> str:
        """Convert migration name to class name"""
        return ''.join(word.capitalize() for word in re.split(r'[_\-\s]+', name))
    
    def _load_migration_file(self, filepath: Path) -> Migration:
        """Load migration from file"""
        spec = importlib.util.spec_from_file_location("migration", filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find migration class
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, Migration) and 
                attr != Migration):
                return attr()
        
        raise ValueError(f"No migration class found in {filepath}")
    
    def _get_migration_files(self) -> List[Path]:
        """Get all migration files sorted by version"""
        files = []
        for file in self.migrations_dir.glob("*.py"):
            if not file.name.startswith("__"):
                files.append(file)
        return sorted(files)
    
    async def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations"""
        applied_versions = await self._get_applied_versions()
        pending = []
        
        for filepath in self._get_migration_files():
            migration = self._load_migration_file(filepath)
            if migration.version not in applied_versions:
                pending.append(migration)
        
        return pending
    
    async def _get_applied_versions(self) -> set:
        """Get set of applied migration versions"""
        try:
            sql = "SELECT version FROM migration_history WHERE status = ?"
            rows = await self.db_adapter.fetch_all(sql, ("applied",))
            return {row["version"] for row in rows}
        except:
            return set()
    
    async def migrate(self, target_version: Optional[str] = None) -> List[MigrationRecord]:
        """Apply migrations up to target version"""
        pending = await self.get_pending_migrations()
        
        if target_version:
            pending = [m for m in pending if m.version <= target_version]
        
        results = []
        for migration in pending:
            result = await self._apply_migration(migration)
            results.append(result)
            if result.status == MigrationStatus.FAILED:
                break
        
        return results
    
    async def _apply_migration(self, migration: Migration) -> MigrationRecord:
        """Apply a single migration with proper transaction handling"""
        start_time = datetime.now()
        
        try:
            await self.db_adapter.begin_transaction()
            
            # Execute migration
            await self.db_adapter.execute_sql(migration.up())
            
            # Record migration with parameterized query
            record = MigrationRecord(
                version=migration.version,
                name=migration.name,
                applied_at=start_time,
                status=MigrationStatus.APPLIED,
                checksum=migration.get_checksum(),
                execution_time=(datetime.now() - start_time).total_seconds(),
                rollback_sql=migration.down()
            )
            
            await self._save_migration_record(record)
            await self.db_adapter.commit_transaction()
            
            return record
            
        except Exception as e:
            await self.db_adapter.rollback_transaction()
            
            record = MigrationRecord(
                version=migration.version,
                name=migration.name,
                applied_at=start_time,
                status=MigrationStatus.FAILED,
                checksum=migration.get_checksum(),
                execution_time=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )
            
            return record
    
    async def rollback(self, target_version: str) -> List[MigrationRecord]:
        """Rollback migrations to target version"""
        applied_migrations = await self._get_applied_migrations_desc()
        
        results = []
        for migration_record in applied_migrations:
            if migration_record.version <= target_version:
                break
            
            result = await self._rollback_migration(migration_record)
            results.append(result)
            
            if result.status == MigrationStatus.FAILED:
                break
        
        return results
    
    async def _get_applied_migrations_desc(self) -> List[MigrationRecord]:
        """Get applied migrations in descending order"""
        sql = """\n        SELECT * FROM migration_history \n        WHERE status = ? \n        ORDER BY version DESC\n        """
        rows = await self.db_adapter.fetch_all(sql, ("applied",))
        
        return [MigrationRecord(
            version=row["version"],
            name=row["name"],
            applied_at=datetime.fromisoformat(row["applied_at"].replace('Z', '+00:00')) 
                if isinstance(row["applied_at"], str) else row["applied_at"],
            status=MigrationStatus(row["status"]),
            checksum=row["checksum"],
            execution_time=row["execution_time"],
            rollback_sql=row["rollback_sql"],
            error_message=row["error_message"]
        ) for row in rows]
    
    async def _rollback_migration(self, migration_record: MigrationRecord) -> MigrationRecord:
        """Rollback a single migration"""
        start_time = datetime.now()
        
        try:
            await self.db_adapter.begin_transaction()
            
            # Execute rollback SQL
            if migration_record.rollback_sql:
                await self.db_adapter.execute_sql(migration_record.rollback_sql)
            
            # Update migration record with parameterized query
            sql = "UPDATE migration_history SET status = ? WHERE version = ?"
            await self.db_adapter.execute_sql(sql, ("rolled_back", migration_record.version))
            
            await self.db_adapter.commit_transaction()
            
            return MigrationRecord(
                version=migration_record.version,
                name=migration_record.name,
                applied_at=start_time,
                status=MigrationStatus.ROLLED_BACK,
                checksum=migration_record.checksum,
                execution_time=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            await self.db_adapter.rollback_transaction()
            
            return MigrationRecord(
                version=migration_record.version,
                name=migration_record.name,
                applied_at=start_time,
                status=MigrationStatus.FAILED,
                checksum=migration_record.checksum,
                execution_time=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )
    
    async def _save_migration_record(self, record: MigrationRecord):
        """Save migration record to database with parameterized query"""
        sql = """\n        INSERT INTO migration_history \n        (version, name, applied_at, status, checksum, execution_time, rollback_sql, error_message)\n        VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n        """
        
        # Format placeholders based on database type
        placeholders = [self.db_adapter.format_placeholder(i+1) for i in range(8)]
        sql = sql.replace("?", "{}").format(*placeholders)
        
        params = (
            record.version, 
            record.name, 
            record.applied_at, 
            record.status.value,
            record.checksum, 
            record.execution_time, 
            record.rollback_sql, 
            record.error_message
        )
        
        await self.db_adapter.execute_sql(sql, params)
    
    async def get_migration_status(self) -> Dict:
        """Get current migration status"""
        try:
            applied = await self.db_adapter.fetch_all(
                "SELECT * FROM migration_history ORDER BY version"
            )
            pending = await self.get_pending_migrations()
            
            return {
                "applied_count": len(applied),
                "pending_count": len(pending),
                "last_applied": applied[-1]["version"] if applied else None,
                "next_pending": pending[0].version if pending else None,
                "applied_migrations": applied,
                "pending_migrations": [{"version": m.version, "name": m.name} for m in pending]
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def close(self):
        """Close database connection"""
        await self.db_adapter.close()