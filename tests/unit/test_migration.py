"""
Unit tests for Migration class.
"""

import pytest
from db_migration_manager.core.migration import Migration


class TestMigration:
    """Test cases for Migration class."""
    
    def test_migration_creation(self):
        """Test basic migration creation."""
        migration = Migration("20240101_120000", "test_migration")
        
        assert migration.version == "20240101_120000"
        assert migration.name == "test_migration"
        assert migration.up_sql == ""
        assert migration.down_sql == ""
    
    def test_migration_with_sql(self):
        """Test migration with SQL statements."""
        migration = Migration("20240101_120000", "create_users")
        migration.up_sql = "CREATE TABLE users (id INTEGER PRIMARY KEY);"
        migration.down_sql = "DROP TABLE users;"
        
        assert migration.up() == "CREATE TABLE users (id INTEGER PRIMARY KEY);"
        assert migration.down() == "DROP TABLE users;"
    
    def test_migration_checksum(self):
        """Test migration checksum generation."""
        migration = Migration("20240101_120000", "test_migration")
        migration.up_sql = "CREATE TABLE test (id INTEGER);"
        migration.down_sql = "DROP TABLE test;"
        
        checksum1 = migration.get_checksum()
        checksum2 = migration.get_checksum()
        
        # Checksums should be deterministic
        assert checksum1 == checksum2
        assert len(checksum1) > 0
    
    def test_migration_checksum_is_string(self):
        """Test that checksum returns a string."""
        migration = Migration("20240101_120000", "test")
        checksum = migration.get_checksum()
        
        assert isinstance(checksum, str)
        assert len(checksum) > 0
    
    def test_migration_version_format(self):
        """Test migration version format."""
        migration = Migration("20240101_120000", "test")
        
        assert len(migration.version) == 15
        assert "_" in migration.version
        assert migration.version.startswith("2024")
    
    def test_migration_name_format(self):
        """Test migration name format."""
        migration = Migration("20240101_120000", "create_users_table")
        
        assert migration.name == "create_users_table"
        assert isinstance(migration.name, str)
        assert len(migration.name) > 0
    
    def test_migration_sql_methods(self):
        """Test up() and down() methods."""
        migration = Migration("20240101_120000", "test")
        
        # Test empty SQL
        assert migration.up() == ""
        assert migration.down() == ""
        
        # Test with SQL
        migration.up_sql = "CREATE TABLE test (id INTEGER);"
        migration.down_sql = "DROP TABLE test;"
        
        assert migration.up() == "CREATE TABLE test (id INTEGER);"
        assert migration.down() == "DROP TABLE test;"
    
    def test_migration_multiline_sql(self):
        """Test migration with multiline SQL."""
        migration = Migration("20240101_120000", "test")
        
        multiline_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE
        );
        """
        
        migration.up_sql = multiline_sql
        assert migration.up() == multiline_sql
    
    def test_migration_empty_sql(self):
        """Test migration with empty SQL."""
        migration = Migration("20240101_120000", "empty_migration")
        
        assert migration.up_sql == ""
        assert migration.down_sql == ""
        assert migration.up() == ""
        assert migration.down() == ""