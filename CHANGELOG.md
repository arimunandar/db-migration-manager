# Changelog

All notable changes to the db-migration-manager project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-01-XX

### Added
- **Pydantic Model Support**: Complete integration for creating migrations from Pydantic models
  - `PydanticMigration` class for model-based migrations
  - `PydanticSchemaGenerator` for converting models to SQL DDL
  - `SchemaComparator` for automatic schema diffing
  - `DatabaseModel` base class with database-specific functionality
  - Database field annotations: `primary_key()`, `unique_field()`, `indexed_field()`, `db_field()`
  - Support for all major Python types with automatic SQL type mapping
  - JSON field support (JSONB for PostgreSQL, JSON for MySQL, TEXT for SQLite)
  - Enum support with VARCHAR storage
  - Custom table naming via `__table_name__` attribute

- **Extended Migration Manager**: 
  - `create_migration_from_models()` method for generating migrations from Pydantic models
  - `validate_models_schema()` method for model validation
  - Automatic schema snapshots for migration diffing
  - Support for auto-diff generation between model versions

- **Enhanced CLI Commands**:
  - `create-from-models` - Create migrations from Pydantic models
  - `validate-models` - Validate Pydantic models for database compatibility  
  - `show-sql` - Display generated SQL for models
  - Support for loading models from Python modules

- **Extended FastAPI API**:
  - `/migrations/create-from-models` endpoint
  - `/migrations/validate-models` endpoint  
  - `/migrations/show-sql` endpoint
  - Enhanced request/response models for Pydantic integration

- **Type Mapping System**: Comprehensive type mapping for PostgreSQL, MySQL, and SQLite
- **Index and Constraint Support**: Full support for database indexes and constraints via annotations
- **Schema Validation**: Built-in validation for model compatibility and best practices

### Changed
- Added Pydantic as a core dependency
- Extended all adapters to work seamlessly with generated SQL
- Enhanced migration file generation to support Pydantic migrations
- Improved error handling and validation throughout the system

### Dependencies
- Added `pydantic>=2.0.0` as core dependency
- All existing dependencies remain unchanged
- Maintains backward compatibility with existing migration workflows

## [1.1.0] - 2024-12-19

### Added
- Comprehensive test suite with 26+ test cases
- Unit tests for Migration class with 100% coverage
- Unit tests for MigrationRecord and MigrationStatus models
- Integration tests for core functionality 
- Test coverage reporting with pytest-cov
- Author information updated to Ari Munandar (arimunandar.dev@gmail.com)

### Enhanced
- Migration checksum validation and integrity checks
- Migration ordering and version format validation
- SQL method testing for up/down operations
- Mock database operations testing for async patterns
- Error handling validation in migration records

### Technical
- Added pytest configuration with asyncio support
- Test fixtures for temporary databases and directories  
- Coverage reporting configured at 30% baseline
- CI-ready test structure for future automation

### Developer Experience
- Clear test organization with unit and integration separation
- Comprehensive test documentation and examples
- Migration name pattern validation
- Version format consistency checks

## [1.0.0] - 2024-12-19

### Added
- Initial release of db-migration-manager
- ORM-agnostic database migration system
- Support for PostgreSQL, MySQL, and SQLite databases
- FastAPI integration with REST endpoints
- CLI interface using Click framework
- Transaction safety and rollback capabilities
- Migration history tracking and status management
- Security enhancements with parameterized queries
- Comprehensive documentation and examples

### Features
- Database adapter pattern for multiple database support
- Async/await support throughout the codebase
- Migration file generation and management
- Migration status tracking (pending, applied, failed, rolled_back)
- Checksum validation for migration integrity
- Rollback functionality to specific versions
- CLI commands: status, migrate, rollback, create

### Security
- SQL injection prevention through parameterized queries
- Transaction management for data consistency
- Error handling and recovery mechanisms