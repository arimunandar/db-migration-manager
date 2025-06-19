"""
Basic integration tests for core functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock

from db_migration_manager.core.migration import Migration
from db_migration_manager.core.models import MigrationStatus


class TestBasicIntegration:
    """Basic integration tests."""
    
    def test_migration_creation_and_checksum(self):
        """Test creating migrations and generating checksums."""
        migration1 = Migration("20240101_120000", "create_users")
        migration1.up_sql = "CREATE TABLE users (id INTEGER PRIMARY KEY);"
        migration1.down_sql = "DROP TABLE users;"
        
        migration2 = Migration("20240101_130000", "add_email")
        migration2.up_sql = "ALTER TABLE users ADD COLUMN email TEXT;"
        migration2.down_sql = "ALTER TABLE users DROP COLUMN email;"
        
        # Checksums should be deterministic
        checksum1_a = migration1.get_checksum()
        checksum1_b = migration1.get_checksum()
        assert checksum1_a == checksum1_b
        
        # Different migrations should have different checksums
        checksum2 = migration2.get_checksum()
        assert checksum1_a != checksum2
        
    def test_migration_status_enum(self):
        """Test migration status enum functionality."""
        assert MigrationStatus.PENDING.value == "pending"
        assert MigrationStatus.APPLIED.value == "applied"
        assert MigrationStatus.FAILED.value == "failed"
        assert MigrationStatus.ROLLED_BACK.value == "rolled_back"
        
        # Test enum comparison
        assert MigrationStatus.PENDING != MigrationStatus.APPLIED
        assert MigrationStatus.APPLIED == MigrationStatus.APPLIED
        
    def test_migration_ordering(self):
        """Test that migrations can be properly ordered by version."""
        migrations = [
            Migration("20240101_130000", "second"),
            Migration("20240101_120000", "first"),
            Migration("20240101_140000", "third"),
        ]
        
        # Sort by version
        sorted_migrations = sorted(migrations, key=lambda m: m.version)
        
        assert sorted_migrations[0].name == "first"
        assert sorted_migrations[1].name == "second"
        assert sorted_migrations[2].name == "third"
    
    def test_migration_sql_methods(self):
        """Test migration SQL generation methods."""
        migration = Migration("20240101_120000", "test")
        migration.up_sql = "CREATE TABLE test (id INTEGER);"
        migration.down_sql = "DROP TABLE test;"
        
        # Test up/down methods
        assert migration.up() == "CREATE TABLE test (id INTEGER);"
        assert migration.down() == "DROP TABLE test;"
        
        # Test with empty SQL
        empty_migration = Migration("20240101_130000", "empty")
        assert empty_migration.up() == ""
        assert empty_migration.down() == ""
    
    @pytest.mark.asyncio 
    async def test_mock_database_operations(self):
        """Test with mock database operations to verify integration patterns."""
        # Mock database adapter
        mock_adapter = AsyncMock()
        mock_adapter.execute_sql.return_value = 1
        mock_adapter.fetch_all.return_value = []
        mock_adapter.get_all_tables.return_value = ["migration_history"]
        
        # Test that our patterns work with async operations
        migration = Migration("20240101_120000", "test")
        migration.up_sql = "CREATE TABLE test (id INTEGER);"
        
        # Simulate applying migration
        result = await mock_adapter.execute_sql(migration.up())
        assert result == 1
        
        # Verify calls were made correctly
        mock_adapter.execute_sql.assert_called_once_with("CREATE TABLE test (id INTEGER);")
    
    def test_version_format_validation(self):
        """Test version format patterns."""
        # Valid version formats
        valid_versions = [
            "20240101_120000",
            "20231225_235959",
            "20240229_000000"  # Leap year
        ]
        
        for version in valid_versions:
            migration = Migration(version, "test")
            assert migration.version == version
            assert len(migration.version) == 15  # YYYYMMDD_HHMMSS
            assert "_" in migration.version
        
    def test_migration_name_patterns(self):
        """Test common migration name patterns."""
        name_patterns = [
            "create_users_table",
            "add_email_to_users", 
            "remove_old_column",
            "create_index_on_email",
            "update_user_permissions"
        ]
        
        for name in name_patterns:
            migration = Migration("20240101_120000", name)
            assert migration.name == name
            assert isinstance(migration.name, str)
            assert len(migration.name) > 0