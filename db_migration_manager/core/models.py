"""
Core data models for the migration system
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class MigrationStatus(Enum):
    """Status of a migration"""
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class MigrationRecord:
    """Record of a migration execution"""
    version: str
    name: str
    applied_at: datetime
    status: MigrationStatus
    checksum: str
    execution_time: float
    rollback_sql: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "version": self.version,
            "name": self.name,
            "applied_at": self.applied_at.isoformat(),
            "status": self.status.value,
            "checksum": self.checksum,
            "execution_time": self.execution_time,
            "rollback_sql": self.rollback_sql,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MigrationRecord":
        """Create from dictionary"""
        return cls(
            version=data["version"],
            name=data["name"],
            applied_at=datetime.fromisoformat(data["applied_at"]),
            status=MigrationStatus(data["status"]),
            checksum=data["checksum"],
            execution_time=data["execution_time"],
            rollback_sql=data.get("rollback_sql"),
            error_message=data.get("error_message")
        )