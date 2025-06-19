# Changelog

All notable changes to the db-migration-manager project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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