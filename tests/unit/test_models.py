"""
Unit tests for core models.
"""

import pytest
from datetime import datetime
from db_migration_manager.core.models import MigrationRecord, MigrationStatus


class TestMigrationStatus:
    """Test cases for MigrationStatus enum."""
    
    def test_status_values(self):
        """Test that all status values are correct."""
        assert MigrationStatus.PENDING.value == "pending"
        assert MigrationStatus.APPLIED.value == "applied"
        assert MigrationStatus.FAILED.value == "failed"
        assert MigrationStatus.ROLLED_BACK.value == "rolled_back"
    
    def test_status_enum_members(self):
        """Test that enum has all expected members."""
        expected_members = {"PENDING", "APPLIED", "FAILED", "ROLLED_BACK"}
        actual_members = {member.name for member in MigrationStatus}
        assert actual_members == expected_members
    
    def test_status_comparison(self):
        """Test enum value comparison."""
        assert MigrationStatus.PENDING != MigrationStatus.APPLIED
        assert MigrationStatus.APPLIED == MigrationStatus.APPLIED
        assert MigrationStatus.FAILED != MigrationStatus.ROLLED_BACK


class TestMigrationRecord:
    """Test cases for MigrationRecord dataclass."""
    
    def test_record_creation_minimal(self):
        """Test creating a minimal migration record."""
        now = datetime.now()
        record = MigrationRecord(
            version="20240101_120000",
            name="test_migration",
            applied_at=now,
            status=MigrationStatus.PENDING
        )
        
        assert record.version == "20240101_120000"
        assert record.name == "test_migration"
        assert record.applied_at == now
        assert record.status == MigrationStatus.PENDING
        assert record.checksum is None
        assert record.execution_time is None
        assert record.error_message is None
        assert record.rollback_sql is None
    
    def test_record_creation_full(self):
        """Test creating a complete migration record."""
        now = datetime.now()
        record = MigrationRecord(
            version="20240101_120000",
            name="test_migration",
            applied_at=now,
            status=MigrationStatus.APPLIED,
            checksum="abc123",
            execution_time=1.5,
            error_message=None,
            rollback_sql="DROP TABLE test;"
        )
        
        assert record.version == "20240101_120000"
        assert record.name == "test_migration"
        assert record.applied_at == now
        assert record.status == MigrationStatus.APPLIED
        assert record.checksum == "abc123"
        assert record.execution_time == 1.5
        assert record.error_message is None
        assert record.rollback_sql == "DROP TABLE test;"
    
    def test_record_with_error(self):
        """Test migration record with error."""
        now = datetime.now()
        record = MigrationRecord(
            version="20240101_120000",
            name="failed_migration",
            applied_at=now,
            status=MigrationStatus.FAILED,
            error_message="Table already exists"
        )
        
        assert record.status == MigrationStatus.FAILED
        assert record.error_message == "Table already exists"
    
    def test_record_status_types(self):
        """Test all migration status types in records."""
        now = datetime.now()
        
        statuses = [
            MigrationStatus.PENDING,
            MigrationStatus.APPLIED,
            MigrationStatus.FAILED,
            MigrationStatus.ROLLED_BACK
        ]
        
        for status in statuses:
            record = MigrationRecord(
                version=f"20240101_12000{status.value[0]}",
                name=f"test_{status.value}",
                applied_at=now,
                status=status
            )
            assert record.status == status
    
    def test_record_execution_time_types(self):
        """Test different execution time types."""
        now = datetime.now()
        
        # Test with int
        record1 = MigrationRecord(
            version="20240101_120000",
            name="test1",
            applied_at=now,
            status=MigrationStatus.APPLIED,
            execution_time=5
        )
        assert record1.execution_time == 5
        
        # Test with float
        record2 = MigrationRecord(
            version="20240101_120001",
            name="test2",
            applied_at=now,
            status=MigrationStatus.APPLIED,
            execution_time=2.5
        )
        assert record2.execution_time == 2.5
        
        # Test with None
        record3 = MigrationRecord(
            version="20240101_120002",
            name="test3",
            applied_at=now,
            status=MigrationStatus.PENDING,
            execution_time=None
        )
        assert record3.execution_time is None
    
    def test_record_dataclass_methods(self):
        """Test dataclass auto-generated methods."""
        now = datetime.now()
        
        record1 = MigrationRecord(
            version="20240101_120000",
            name="test",
            applied_at=now,
            status=MigrationStatus.APPLIED
        )
        
        record2 = MigrationRecord(
            version="20240101_120000",
            name="test",
            applied_at=now,
            status=MigrationStatus.APPLIED
        )
        
        # Test equality
        assert record1 == record2
        
        # Test string representation contains key fields
        record_str = str(record1)
        assert "20240101_120000" in record_str
        assert "test" in record_str
        assert "APPLIED" in record_str
    
    def test_record_different_versions(self):
        """Test records with different versions are not equal."""
        now = datetime.now()
        
        record1 = MigrationRecord(
            version="20240101_120000",
            name="test",
            applied_at=now,
            status=MigrationStatus.APPLIED
        )
        
        record2 = MigrationRecord(
            version="20240101_130000",
            name="test",
            applied_at=now,
            status=MigrationStatus.APPLIED
        )
        
        assert record1 != record2