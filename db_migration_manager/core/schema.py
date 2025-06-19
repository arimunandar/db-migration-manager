"""
Schema generation and comparison for Pydantic models
"""

import inspect
from typing import Dict, List, Optional, Set, Type, Union, get_args, get_origin
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo


class TableDefinition:
    """Represents a database table definition"""
    
    def __init__(self, name: str, columns: List['ColumnDefinition'], 
                 indexes: Optional[List['IndexDefinition']] = None,
                 constraints: Optional[List['ConstraintDefinition']] = None):
        self.name = name
        self.columns = columns
        self.indexes = indexes or []
        self.constraints = constraints or []
    
    def to_create_sql(self, dialect: str = 'postgresql') -> str:
        """Generate CREATE TABLE SQL"""
        columns_sql = []
        
        for column in self.columns:
            columns_sql.append(column.to_sql(dialect))
        
        # Add constraints
        for constraint in self.constraints:
            columns_sql.append(constraint.to_sql(dialect))
        
        table_sql = f"CREATE TABLE {self.name} (\n    " + ",\n    ".join(columns_sql) + "\n)"
        
        # Add indexes as separate statements
        if self.indexes:
            index_sqls = [index.to_sql(dialect, self.name) for index in self.indexes]
            table_sql += ";\n\n" + ";\n".join(index_sqls) + ";"
        
        return table_sql
    
    def to_drop_sql(self, dialect: str = 'postgresql') -> str:
        """Generate DROP TABLE SQL"""
        return f"DROP TABLE IF EXISTS {self.name}"


class ColumnDefinition:
    """Represents a database column definition"""
    
    def __init__(self, name: str, sql_type: str, nullable: bool = True, 
                 default: Optional[str] = None, primary_key: bool = False,
                 unique: bool = False, auto_increment: bool = False):
        self.name = name
        self.sql_type = sql_type
        self.nullable = nullable
        self.default = default
        self.primary_key = primary_key
        self.unique = unique
        self.auto_increment = auto_increment
    
    def to_sql(self, dialect: str = 'postgresql') -> str:
        """Generate column SQL"""
        parts = [self.name, self.sql_type]
        
        if self.primary_key:
            parts.append("PRIMARY KEY")
        
        if self.auto_increment:
            if dialect == 'postgresql':
                # For PostgreSQL, use SERIAL or BIGSERIAL
                if 'INT' in self.sql_type.upper():
                    parts[1] = 'SERIAL' if 'BIGINT' not in self.sql_type.upper() else 'BIGSERIAL'
            elif dialect == 'mysql':
                parts.append("AUTO_INCREMENT")
            elif dialect == 'sqlite':
                parts.append("AUTOINCREMENT")
        
        if not self.nullable and not self.primary_key:
            parts.append("NOT NULL")
        
        if self.unique and not self.primary_key:
            parts.append("UNIQUE")
        
        if self.default is not None:
            parts.append(f"DEFAULT {self.default}")
        
        return " ".join(parts)


class IndexDefinition:
    """Represents a database index definition"""
    
    def __init__(self, name: str, columns: List[str], unique: bool = False):
        self.name = name
        self.columns = columns
        self.unique = unique
    
    def to_sql(self, dialect: str, table_name: str) -> str:
        """Generate index SQL"""
        index_type = "UNIQUE INDEX" if self.unique else "INDEX"
        columns_str = ", ".join(self.columns)
        return f"CREATE {index_type} {self.name} ON {table_name} ({columns_str})"


class ConstraintDefinition:
    """Represents a database constraint definition"""
    
    def __init__(self, name: str, constraint_type: str, definition: str):
        self.name = name
        self.constraint_type = constraint_type
        self.definition = definition
    
    def to_sql(self, dialect: str) -> str:
        """Generate constraint SQL"""
        return f"CONSTRAINT {self.name} {self.definition}"


class PydanticSchemaGenerator:
    """Generates database schema from Pydantic models"""
    
    def __init__(self, dialect: str = 'postgresql'):
        self.dialect = dialect
        self.type_mapping = self._get_type_mapping()
    
    def _get_type_mapping(self) -> Dict[Type, str]:
        """Get type mapping for the current dialect"""
        if self.dialect == 'postgresql':
            return {
                str: 'VARCHAR(255)',
                int: 'INTEGER',
                float: 'DOUBLE PRECISION',
                bool: 'BOOLEAN',
                datetime: 'TIMESTAMP',
                date: 'DATE',
                Decimal: 'DECIMAL',
                bytes: 'BYTEA',
            }
        elif self.dialect == 'mysql':
            return {
                str: 'VARCHAR(255)',
                int: 'INT',
                float: 'DOUBLE',
                bool: 'TINYINT(1)',
                datetime: 'DATETIME',
                date: 'DATE',
                Decimal: 'DECIMAL',
                bytes: 'BLOB',
            }
        elif self.dialect == 'sqlite':
            return {
                str: 'TEXT',
                int: 'INTEGER',
                float: 'REAL',
                bool: 'INTEGER',
                datetime: 'TIMESTAMP',
                date: 'DATE',
                Decimal: 'DECIMAL',
                bytes: 'BLOB',
            }
        else:
            raise ValueError(f"Unsupported dialect: {self.dialect}")
    
    def generate_table_from_model(self, model: Type[BaseModel], 
                                  table_name: Optional[str] = None) -> TableDefinition:
        """Generate table definition from Pydantic model"""
        if table_name is None:
            table_name = model.__name__.lower()
        
        columns = []
        indexes = []
        constraints = []
        
        # Check if model has a custom table name
        if hasattr(model, '__table_name__'):
            table_name = model.__table_name__
        
        # Get all fields from the model
        for field_name, field_info in model.model_fields.items():
            column = self._field_to_column(field_name, field_info)
            columns.append(column)
            
            # Check for index annotations
            if hasattr(field_info, 'json_schema_extra') and field_info.json_schema_extra:
                extra = field_info.json_schema_extra
                if isinstance(extra, dict):
                    if extra.get('index'):
                        indexes.append(IndexDefinition(
                            name=f"idx_{table_name}_{field_name}",
                            columns=[field_name],
                            unique=extra.get('unique_index', False)
                        ))
        
        return TableDefinition(table_name, columns, indexes, constraints)
    
    def _field_to_column(self, field_name: str, field_info: FieldInfo) -> ColumnDefinition:
        """Convert Pydantic field to column definition"""
        # Get the field type
        field_type = field_info.annotation
        
        # Handle Optional types
        nullable = True
        if get_origin(field_type) is Union:
            args = get_args(field_type)
            if len(args) == 2 and type(None) in args:
                # This is Optional[T]
                field_type = args[0] if args[1] is type(None) else args[1]
                nullable = True
            else:
                nullable = False
        else:
            nullable = field_info.default is not None or field_info.default_factory is not None
        
        # Handle required fields
        if field_info.default is ... and field_info.default_factory is None:
            nullable = False
        
        # Get SQL type
        sql_type = self._python_type_to_sql(field_type, field_info)
        
        # Check for special annotations
        primary_key = False
        unique = False
        auto_increment = False
        default_value = None
        
        if hasattr(field_info, 'json_schema_extra') and field_info.json_schema_extra:
            extra = field_info.json_schema_extra
            if isinstance(extra, dict):
                primary_key = extra.get('primary_key', False)
                unique = extra.get('unique', False)
                auto_increment = extra.get('auto_increment', False)
        
        # Handle default values
        if field_info.default is not None and field_info.default is not ... and not callable(field_info.default):
            # Skip PydanticUndefined values
            if str(field_info.default) == 'PydanticUndefined':
                default_value = None
            elif isinstance(field_info.default, str):
                default_value = f"'{field_info.default}'"
            elif isinstance(field_info.default, bool):
                default_value = str(field_info.default).upper()
            else:
                default_value = str(field_info.default)
        elif field_info.default_factory is not None:
            # For fields with default_factory, we don't set a database default
            default_value = None
        
        return ColumnDefinition(
            name=field_name,
            sql_type=sql_type,
            nullable=nullable,
            default=default_value,
            primary_key=primary_key,
            unique=unique,
            auto_increment=auto_increment
        )
    
    def _python_type_to_sql(self, python_type: Type, field_info: FieldInfo) -> str:
        """Convert Python type to SQL type"""
        # Handle basic types
        if python_type in self.type_mapping:
            sql_type = self.type_mapping[python_type]
            
            # Handle string length constraints
            if python_type is str and hasattr(field_info, 'json_schema_extra'):
                extra = field_info.json_schema_extra
                if isinstance(extra, dict) and 'max_length' in extra:
                    if self.dialect in ['postgresql', 'mysql']:
                        sql_type = f"VARCHAR({extra['max_length']})"
                    # SQLite uses TEXT regardless of length
            
            return sql_type
        
        # Handle Enum types
        if inspect.isclass(python_type) and issubclass(python_type, Enum):
            if self.dialect == 'postgresql':
                # Could create ENUM type, but VARCHAR is simpler for cross-compatibility
                return 'VARCHAR(50)'
            else:
                return 'VARCHAR(50)'
        
        # Handle List types (stored as JSON)
        if get_origin(python_type) is list:
            if self.dialect == 'postgresql':
                return 'JSONB'
            elif self.dialect == 'mysql':
                return 'JSON'
            else:
                return 'TEXT'
        
        # Handle Dict types (stored as JSON)
        if get_origin(python_type) is dict:
            if self.dialect == 'postgresql':
                return 'JSONB'
            elif self.dialect == 'mysql':
                return 'JSON'
            else:
                return 'TEXT'
        
        # Default to TEXT for unknown types
        return 'TEXT'


class SchemaComparator:
    """Compares database schemas to generate migrations"""
    
    def __init__(self, dialect: str = 'postgresql'):
        self.dialect = dialect
    
    def compare_schemas(self, old_schema: Dict[str, TableDefinition], 
                       new_schema: Dict[str, TableDefinition]) -> List[str]:
        """Compare two schemas and return migration SQL statements"""
        migration_statements = []
        
        # Find new tables
        for table_name in new_schema:
            if table_name not in old_schema:
                migration_statements.append(
                    new_schema[table_name].to_create_sql(self.dialect)
                )
        
        # Find dropped tables
        for table_name in old_schema:
            if table_name not in new_schema:
                migration_statements.append(
                    old_schema[table_name].to_drop_sql(self.dialect)
                )
        
        # Find modified tables
        for table_name in new_schema:
            if table_name in old_schema:
                table_changes = self._compare_tables(
                    old_schema[table_name], 
                    new_schema[table_name]
                )
                migration_statements.extend(table_changes)
        
        return migration_statements
    
    def _compare_tables(self, old_table: TableDefinition, 
                       new_table: TableDefinition) -> List[str]:
        """Compare two table definitions"""
        statements = []
        table_name = new_table.name
        
        # Create column lookup dictionaries
        old_columns = {col.name: col for col in old_table.columns}
        new_columns = {col.name: col for col in new_table.columns}
        
        # Find new columns
        for col_name, column in new_columns.items():
            if col_name not in old_columns:
                statements.append(
                    f"ALTER TABLE {table_name} ADD COLUMN {column.to_sql(self.dialect)}"
                )
        
        # Find dropped columns
        for col_name in old_columns:
            if col_name not in new_columns:
                statements.append(
                    f"ALTER TABLE {table_name} DROP COLUMN {col_name}"
                )
        
        # Find modified columns
        for col_name in new_columns:
            if col_name in old_columns:
                old_col = old_columns[col_name]
                new_col = new_columns[col_name]
                
                if self._columns_differ(old_col, new_col):
                    if self.dialect == 'postgresql':
                        statements.append(
                            f"ALTER TABLE {table_name} ALTER COLUMN {col_name} TYPE {new_col.sql_type}"
                        )
                    elif self.dialect == 'mysql':
                        statements.append(
                            f"ALTER TABLE {table_name} MODIFY COLUMN {new_col.to_sql(self.dialect)}"
                        )
                    elif self.dialect == 'sqlite':
                        # SQLite doesn't support ALTER COLUMN, would need table recreation
                        statements.append(
                            f"-- SQLite doesn't support ALTER COLUMN for {table_name}.{col_name}"
                        )
        
        return statements
    
    def _columns_differ(self, old_col: ColumnDefinition, new_col: ColumnDefinition) -> bool:
        """Check if two columns are different"""
        return (old_col.sql_type != new_col.sql_type or
                old_col.nullable != new_col.nullable or
                old_col.default != new_col.default)


# Utility functions for creating Pydantic fields with database annotations
def db_field(primary_key: bool = False, unique: bool = False, 
             auto_increment: bool = False, index: bool = False,
             unique_index: bool = False, max_length: Optional[int] = None,
             **kwargs) -> FieldInfo:
    """Create a Pydantic field with database annotations"""
    json_schema_extra = {
        'primary_key': primary_key,
        'unique': unique,
        'auto_increment': auto_increment,
        'index': index,
        'unique_index': unique_index,
    }
    
    if max_length is not None:
        json_schema_extra['max_length'] = max_length
    
    return Field(json_schema_extra=json_schema_extra, **kwargs)


def primary_key(**kwargs) -> FieldInfo:
    """Create a primary key field"""
    return db_field(primary_key=True, auto_increment=True, **kwargs)


def unique_field(**kwargs) -> FieldInfo:
    """Create a unique field"""
    return db_field(unique=True, **kwargs)


def indexed_field(**kwargs) -> FieldInfo:
    """Create an indexed field"""
    return db_field(index=True, **kwargs) 