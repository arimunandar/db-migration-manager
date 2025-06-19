"""
Pydantic-based migration classes
"""

import inspect
import json
from typing import Dict, List, Optional, Type, Union

from pydantic import BaseModel

from .migration import Migration
from .schema import PydanticSchemaGenerator, SchemaComparator, TableDefinition


class PydanticMigration(Migration):
    """Migration that can be generated from Pydantic models"""
    
    def __init__(self, version: str, name: str, models: Optional[List[Type[BaseModel]]] = None):
        super().__init__(version, name)
        self.models = models or []
        self.previous_models: Optional[List[Type[BaseModel]]] = None
        self.dialect = 'postgresql'  # Default dialect
        
    def set_dialect(self, dialect: str) -> None:
        """Set the database dialect"""
        self.dialect = dialect
    
    def add_model(self, model: Type[BaseModel]) -> None:
        """Add a Pydantic model to this migration"""
        if model not in self.models:
            self.models.append(model)
    
    def set_previous_models(self, models: List[Type[BaseModel]]) -> None:
        """Set the previous state of models for comparison"""
        self.previous_models = models
    
    def generate_sql(self) -> None:
        """Generate up and down SQL from the models"""
        if self.previous_models is None:
            # This is a new migration - create all tables
            self.up_sql = self._generate_create_sql()
            self.down_sql = self._generate_drop_sql()
        else:
            # This is a modification - compare with previous state
            self.up_sql, self.down_sql = self._generate_diff_sql()
    
    def _generate_create_sql(self) -> str:
        """Generate SQL to create all tables from models"""
        generator = PydanticSchemaGenerator(self.dialect)
        statements = []
        
        for model in self.models:
            table_def = generator.generate_table_from_model(model)
            sql = table_def.to_create_sql(self.dialect)
            # Split multi-statement SQL into individual statements
            individual_statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
            statements.extend(individual_statements)
        
        return ";\n".join(statements) + ";" if statements else ""
    
    def _generate_drop_sql(self) -> str:
        """Generate SQL to drop all tables"""
        statements = []
        
        # Drop in reverse order to handle dependencies
        for model in reversed(self.models):
            table_name = getattr(model, '__table_name__', model.__name__.lower())
            statements.append(f"DROP TABLE IF EXISTS {table_name}")
        
        return ";\n".join(statements) + ";" if statements else ""
    
    def _generate_diff_sql(self) -> tuple[str, str]:
        """Generate SQL by comparing with previous models"""
        generator = PydanticSchemaGenerator(self.dialect)
        comparator = SchemaComparator(self.dialect)
        
        # Generate schema definitions
        old_schema = {}
        new_schema = {}
        
        if self.previous_models:
            for model in self.previous_models:
                table_def = generator.generate_table_from_model(model)
                old_schema[table_def.name] = table_def
        
        for model in self.models:
            table_def = generator.generate_table_from_model(model)
            new_schema[table_def.name] = table_def
        
        # Generate migration statements
        up_statements = comparator.compare_schemas(old_schema, new_schema)
        down_statements = comparator.compare_schemas(new_schema, old_schema)
        
        up_sql = ";\n".join(up_statements) + ";" if up_statements else ""
        down_sql = ";\n".join(down_statements) + ";" if down_statements else ""
        
        return up_sql, down_sql
    
    def save_models_snapshot(self, filepath: str) -> None:
        """Save a snapshot of the current models for future comparison"""
        snapshot = {
            'version': self.version,
            'models': []
        }
        
        for model in self.models:
            model_info = {
                'name': model.__name__,
                'module': model.__module__,
                'fields': {},
                'table_name': getattr(model, '__table_name__', model.__name__.lower())
            }
            
            # Serialize field information
            for field_name, field_info in model.model_fields.items():
                field_data = {
                    'type': str(field_info.annotation),
                    'default': str(field_info.default) if field_info.default is not ... else None,
                    'nullable': field_info.default is not ... or field_info.default_factory is not None
                }
                
                if hasattr(field_info, 'json_schema_extra') and field_info.json_schema_extra:
                    field_data['extra'] = field_info.json_schema_extra
                
                model_info['fields'][field_name] = field_data
            
            snapshot['models'].append(model_info)
        
        with open(filepath, 'w') as f:
            json.dump(snapshot, f, indent=2)
    
    @classmethod
    def load_models_snapshot(cls, filepath: str) -> Dict:
        """Load a models snapshot from file"""
        with open(filepath, 'r') as f:
            return json.load(f)


class ModelMigrationBuilder:
    """Helper class to build migrations from Pydantic models"""
    
    def __init__(self, dialect: str = 'postgresql'):
        self.dialect = dialect
        self.models: List[Type[BaseModel]] = []
        self.previous_snapshot: Optional[Dict] = None
    
    def add_model(self, model: Type[BaseModel]) -> 'ModelMigrationBuilder':
        """Add a model to the migration"""
        self.models.append(model)
        return self
    
    def add_models(self, models: List[Type[BaseModel]]) -> 'ModelMigrationBuilder':
        """Add multiple models to the migration"""
        self.models.extend(models)
        return self
    
    def set_previous_snapshot(self, snapshot_path: str) -> 'ModelMigrationBuilder':
        """Set the previous models snapshot for comparison"""
        self.previous_snapshot = PydanticMigration.load_models_snapshot(snapshot_path)
        return self
    
    def build(self, version: str, name: str) -> PydanticMigration:
        """Build the migration"""
        migration = PydanticMigration(version, name, self.models)
        migration.set_dialect(self.dialect)
        
        if self.previous_snapshot:
            # TODO: Reconstruct models from snapshot for comparison
            # This would require more complex logic to recreate Pydantic models
            # from the JSON representation
            pass
        
        migration.generate_sql()
        return migration


def create_migration_from_models(
    models: List[Type[BaseModel]], 
    version: str, 
    name: str,
    dialect: str = 'postgresql',
    previous_snapshot: Optional[str] = None
) -> PydanticMigration:
    """
    Convenience function to create a migration from Pydantic models
    
    Args:
        models: List of Pydantic models
        version: Migration version
        name: Migration name
        dialect: Database dialect (postgresql, mysql, sqlite)
        previous_snapshot: Path to previous models snapshot for diff generation
    
    Returns:
        PydanticMigration instance
    """
    builder = ModelMigrationBuilder(dialect)
    builder.add_models(models)
    
    if previous_snapshot:
        builder.set_previous_snapshot(previous_snapshot)
    
    return builder.build(version, name)


# Base model class with convenience methods
class DatabaseModel(BaseModel):
    """Base model class with database-specific functionality"""
    
    class Config:
        # Enable arbitrary types for database-specific fields
        arbitrary_types_allowed = True
    
    @classmethod
    def get_table_name(cls) -> str:
        """Get the table name for this model"""
        return getattr(cls, '__table_name__', cls.__name__.lower())
    
    @classmethod
    def generate_table_sql(cls, dialect: str = 'postgresql') -> str:
        """Generate CREATE TABLE SQL for this model"""
        generator = PydanticSchemaGenerator(dialect)
        table_def = generator.generate_table_from_model(cls)
        return table_def.to_create_sql(dialect)
    
    @classmethod
    def generate_drop_sql(cls, dialect: str = 'postgresql') -> str:
        """Generate DROP TABLE SQL for this model"""
        table_name = cls.get_table_name()
        return f"DROP TABLE IF EXISTS {table_name}" 