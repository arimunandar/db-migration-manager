"""
API response models for FastAPI integration
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel


class MigrationResponse(BaseModel):
    """Standard response model for migration operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    
    @classmethod
    def success_response(cls, message: str, data: Optional[Dict[str, Any]] = None) -> "MigrationResponse":
        """Create a success response"""
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def error_response(cls, message: str, data: Optional[Dict[str, Any]] = None) -> "MigrationResponse":
        """Create an error response"""
        return cls(success=False, message=message, data=data)


class CreateMigrationRequest(BaseModel):
    """Request model for creating migrations"""
    name: str
    up_sql: str = ""
    down_sql: str = ""


class MigrateRequest(BaseModel):
    """Request model for running migrations"""
    target_version: Optional[str] = None


class RollbackRequest(BaseModel):
    """Request model for rolling back migrations"""
    target_version: str