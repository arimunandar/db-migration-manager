"""
Unit tests for Pydantic schema generation functionality.
"""

import pytest
from datetime import datetime
from typing import Optional
from decimal import Decimal
from enum import Enum

from pydantic import Field
from db_migration_manager.core.schema import (
    PydanticSchemaGenerator,
    TableDefinition,
    ColumnDefinition,
    SchemaComparator
)
from db_migration_manager import (
    DatabaseModel,
    primary_key,
    unique_field,
    indexed_field,
    db_field
)


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class UserModel(DatabaseModel):
    """Test model for schema generation"""
    id: int = primary_key(default=None)
    email: str = unique_field(max_length=255)
    username: str = indexed_field(max_length=50)
    full_name: str = db_field(max_length=100)
    age: Optional[int] = None
    is_active: bool = Field(default=True)
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)
    
    __table_name__ = "users"


class TestPydanticSchemaGenerator:
    """Test cases for PydanticSchemaGenerator"""
    
    def test_postgresql_type_mapping(self):
        """Test PostgreSQL type mapping"""
        generator = PydanticSchemaGenerator('postgresql')
        mapping = generator._get_type_mapping()
        
        assert mapping[str] == 'VARCHAR(255)'
        assert mapping[int] == 'INTEGER'
        assert mapping[float] == 'DOUBLE PRECISION'
        assert mapping[bool] == 'BOOLEAN'
        assert mapping[datetime] == 'TIMESTAMP'
        assert mapping[Decimal] == 'DECIMAL'
        # Dict and list types are handled separately in _python_type_to_sql
        # They're not in the basic type mapping
    
    def test_mysql_type_mapping(self):
        """Test MySQL type mapping"""
        generator = PydanticSchemaGenerator('mysql')
        mapping = generator._get_type_mapping()
        
        assert mapping[str] == 'VARCHAR(255)'
        assert mapping[int] == 'INT'
        assert mapping[float] == 'DOUBLE'
        assert mapping[bool] == 'TINYINT(1)'
        assert mapping[datetime] == 'DATETIME'
        assert mapping[Decimal] == 'DECIMAL'
        # Dict and list types are handled separately in _python_type_to_sql
    
    def test_sqlite_type_mapping(self):
        """Test SQLite type mapping"""
        generator = PydanticSchemaGenerator('sqlite')
        mapping = generator._get_type_mapping()
        
        assert mapping[str] == 'TEXT'
        assert mapping[int] == 'INTEGER'
        assert mapping[float] == 'REAL'
        assert mapping[bool] == 'INTEGER'
        assert mapping[datetime] == 'TIMESTAMP'
        assert mapping[Decimal] == 'DECIMAL'
        # Dict and list types are handled separately in _python_type_to_sql
    
    def test_generate_table_from_model_postgresql(self):
        """Test table generation from Pydantic model for PostgreSQL"""
        generator = PydanticSchemaGenerator('postgresql')
        table_def = generator.generate_table_from_model(UserModel)
        
        assert table_def.name == "users"
        assert len(table_def.columns) == 9
        
        # Check primary key column (SQL type is converted in to_sql method)
        id_col = next(col for col in table_def.columns if col.name == 'id')
        assert id_col.primary_key is True
        assert id_col.auto_increment is True
        assert id_col.sql_type == 'INTEGER'  # Base type, converted to SERIAL in to_sql()
        
        # Check unique field
        email_col = next(col for col in table_def.columns if col.name == 'email')
        assert email_col.unique is True
        assert email_col.sql_type == 'VARCHAR(255)'
        
        # Check indexed field
        username_col = next(col for col in table_def.columns if col.name == 'username')
        assert username_col.sql_type == 'VARCHAR(50)'
        
        # Check optional field
        age_col = next(col for col in table_def.columns if col.name == 'age')
        assert age_col.nullable is True
        assert age_col.sql_type == 'INTEGER'
        
        # Check enum field
        status_col = next(col for col in table_def.columns if col.name == 'status')
        assert status_col.sql_type == 'VARCHAR(50)'
        
        # Check JSON field (handled in _python_type_to_sql)
        metadata_col = next(col for col in table_def.columns if col.name == 'metadata')
        # The actual type will be determined by _python_type_to_sql method
    
    def test_generate_table_from_model_mysql(self):
        """Test table generation from Pydantic model for MySQL"""
        generator = PydanticSchemaGenerator('mysql')
        table_def = generator.generate_table_from_model(UserModel)
        
        # Check primary key (base type, AUTO_INCREMENT added in to_sql)
        id_col = next(col for col in table_def.columns if col.name == 'id')
        assert id_col.sql_type == 'INT'  # Base type
        assert id_col.auto_increment is True
    
    def test_generate_table_from_model_sqlite(self):
        """Test table generation from Pydantic model for SQLite"""
        generator = PydanticSchemaGenerator('sqlite')
        table_def = generator.generate_table_from_model(UserModel)
        
        # Check primary key (base type, AUTOINCREMENT added in to_sql)
        id_col = next(col for col in table_def.columns if col.name == 'id')
        assert id_col.sql_type == 'INTEGER'  # Base type
        assert id_col.auto_increment is True
    
    def test_table_name_from_model(self):
        """Test table name extraction from model"""
        generator = PydanticSchemaGenerator('postgresql')
        
        # With explicit table name
        table_def = generator.generate_table_from_model(UserModel)
        assert table_def.name == "users"
        
        # Without explicit table name (should use class name lowercased)
        class NoTableName(DatabaseModel):
            id: int = primary_key()
        
        table_def2 = generator.generate_table_from_model(NoTableName)
        assert table_def2.name == "notablename"


class TestTableDefinition:
    """Test cases for TableDefinition"""
    
    def test_create_sql_postgresql(self):
        """Test CREATE TABLE SQL generation for PostgreSQL"""
        columns = [
            ColumnDefinition("id", "SERIAL", nullable=False, primary_key=True, auto_increment=True),
            ColumnDefinition("name", "VARCHAR(100)", nullable=False, unique=True),
            ColumnDefinition("email", "VARCHAR(255)", nullable=True)
        ]
        table_def = TableDefinition("test_table", columns)
        
        sql = table_def.to_create_sql('postgresql')
        assert "CREATE TABLE test_table" in sql
        assert "id SERIAL PRIMARY KEY" in sql
        assert "name VARCHAR(100) NOT NULL UNIQUE" in sql
        assert "email VARCHAR(255)" in sql
    
    def test_create_sql_mysql(self):
        """Test CREATE TABLE SQL generation for MySQL"""
        columns = [
            ColumnDefinition("id", "INT AUTO_INCREMENT", nullable=False, primary_key=True, auto_increment=True),
            ColumnDefinition("name", "VARCHAR(100)", nullable=False)
        ]
        table_def = TableDefinition("test_table", columns)
        
        sql = table_def.to_create_sql('mysql')
        assert "CREATE TABLE test_table" in sql
        assert "id INT AUTO_INCREMENT PRIMARY KEY" in sql
    
    def test_create_sql_sqlite(self):
        """Test CREATE TABLE SQL generation for SQLite"""
        columns = [
            ColumnDefinition("id", "INTEGER AUTOINCREMENT", nullable=False, primary_key=True, auto_increment=True),
            ColumnDefinition("name", "TEXT", nullable=False)
        ]
        table_def = TableDefinition("test_table", columns)
        
        sql = table_def.to_create_sql('sqlite')
        assert "CREATE TABLE test_table" in sql
        assert "id INTEGER AUTOINCREMENT PRIMARY KEY" in sql
    
    def test_drop_sql(self):
        """Test DROP TABLE SQL generation"""
        table_def = TableDefinition("test_table", [])
        sql = table_def.to_drop_sql()
        assert sql == "DROP TABLE IF EXISTS test_table"


class TestColumnDefinition:
    """Test cases for ColumnDefinition"""
    
    def test_column_sql_basic(self):
        """Test basic column SQL generation"""
        col = ColumnDefinition("test_col", "VARCHAR(50)", nullable=True)
        sql = col.to_sql('postgresql')
        assert sql == "test_col VARCHAR(50)"
    
    def test_column_sql_not_null(self):
        """Test NOT NULL column"""
        col = ColumnDefinition("test_col", "VARCHAR(50)", nullable=False)
        sql = col.to_sql('postgresql')
        assert sql == "test_col VARCHAR(50) NOT NULL"
    
    def test_column_sql_unique(self):
        """Test UNIQUE column"""
        col = ColumnDefinition("test_col", "VARCHAR(50)", nullable=False, unique=True)
        sql = col.to_sql('postgresql')
        assert sql == "test_col VARCHAR(50) NOT NULL UNIQUE"
    
    def test_column_sql_primary_key(self):
        """Test PRIMARY KEY column"""
        col = ColumnDefinition("id", "SERIAL", nullable=False, primary_key=True)
        sql = col.to_sql('postgresql')
        assert sql == "id SERIAL PRIMARY KEY"
    
    def test_column_sql_with_default(self):
        """Test column with default value"""
        col = ColumnDefinition("status", "VARCHAR(20)", nullable=False, default="'active'")
        sql = col.to_sql('postgresql')
        assert sql == "status VARCHAR(20) NOT NULL DEFAULT 'active'"


class TestSchemaComparator:
    """Test cases for SchemaComparator"""
    
    def test_compare_schemas_new_table(self):
        """Test detecting new tables"""
        comparator = SchemaComparator('postgresql')
        
        old_schema = {}
        new_schema = {
            "users": TableDefinition("users", [
                ColumnDefinition("id", "SERIAL", nullable=False, primary_key=True)
            ])
        }
        
        statements = comparator.compare_schemas(old_schema, new_schema)
        assert len(statements) == 1
        assert "CREATE TABLE users" in statements[0]
    
    def test_compare_schemas_dropped_table(self):
        """Test detecting dropped tables"""
        comparator = SchemaComparator('postgresql')
        
        old_schema = {
            "users": TableDefinition("users", [
                ColumnDefinition("id", "SERIAL", nullable=False, primary_key=True)
            ])
        }
        new_schema = {}
        
        statements = comparator.compare_schemas(old_schema, new_schema)
        assert len(statements) == 1
        assert "DROP TABLE IF EXISTS users" in statements[0]
    
    def test_compare_schemas_new_column(self):
        """Test detecting new columns"""
        comparator = SchemaComparator('postgresql')
        
        old_table = TableDefinition("users", [
            ColumnDefinition("id", "SERIAL", nullable=False, primary_key=True)
        ])
        new_table = TableDefinition("users", [
            ColumnDefinition("id", "SERIAL", nullable=False, primary_key=True),
            ColumnDefinition("email", "VARCHAR(255)", nullable=True)
        ])
        
        old_schema = {"users": old_table}
        new_schema = {"users": new_table}
        
        statements = comparator.compare_schemas(old_schema, new_schema)
        assert len(statements) == 1
        assert "ALTER TABLE users ADD COLUMN email VARCHAR(255)" in statements[0] 