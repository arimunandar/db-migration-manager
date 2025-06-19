"""
Base migration class
"""

import hashlib
from typing import List


class Migration:
    """Base migration class"""
    
    def __init__(self, version: str, name: str):
        self.version = version
        self.name = name
        self.up_sql = ""
        self.down_sql = ""
        self.dependencies: List[str] = []
    
    def up(self) -> str:
        """SQL to apply migration"""
        return self.up_sql
    
    def down(self) -> str:
        """SQL to rollback migration"""
        return self.down_sql
    
    def get_checksum(self) -> str:
        """Generate checksum for migration"""
        content = f"{self.version}{self.name}{self.up_sql}{self.down_sql}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_dependencies(self) -> List[str]:
        """Get migration dependencies"""
        return self.dependencies
    
    def add_dependency(self, version: str) -> None:
        """Add a dependency to this migration"""
        if version not in self.dependencies:
            self.dependencies.append(version)
    
    def __str__(self) -> str:
        return f"Migration({self.version}, {self.name})"
    
    def __repr__(self) -> str:
        return self.__str__()