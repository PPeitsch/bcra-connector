# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2024-12-28

### Added
- Comprehensive unit test coverage for all major components
- Extensive integration tests for BCRA API endpoints
- Complete test suite for rate limiter and error handling
- Improved type annotations across test infrastructure
- Detailed test cases for data models and edge cases

### Enhanced
- Test coverage for principales_variables, cheques, and estadisticas_cambiarias modules
- Error handling and rate limiting test scenarios
- Reliability of rate limiter implementation
- Consistency in test suite structure and methodology

### Fixed
- Intermittent test failures in rate limiting tests
- SSL and timeout error handling test coverage
- Type annotation issues in test files
- Flaky test behaviors in CI environment

### Changed
- Improved test suite organization
- Enhanced error message validation
- Refined rate limiter state tracking logic

## [0.4.0] - 2024-11-23

### Added
- Contributor Covenant Code of Conduct
- Structured issue templates for bugs, features, and documentation
- Security policy document
- Pull request template
- GitHub Actions workflow for testing and publishing
- Comprehensive community guidelines
- Automated testing and publishing process

### Enhanced
- Updated README with new badges and improved organization
- Improved contributing guidelines with clear standards
- Enhanced example scripts documentation
- Better error handling and logging
- Project structure and organization
- Documentation system
- Streamlined contribution process

### Fixed
- CI/CD badge display in README
- Documentation inconsistencies
- Build process reliability
- Version tracking system

## [0.3.3] - 2024-11-06

### Added
- Rate limiting functionality with configurable limits and burst support
- Flexible request timeout configuration
- New `RateLimitConfig` class for customizing API rate limits
- New `TimeoutConfig` class for fine-grained timeout control

### Enhanced
- Improved error handling for timeouts and rate limits
- Better logging for request timing and rate limiting events
- Added extensive test coverage for new features

### Changed
- Updated default timeout values for better reliability
- Improved request handling with separate connect and read timeouts

## [0.3.2] - 2024-11-06

### Changed
- Improved code organization and modularity
- Enhanced version management system with better validation
- Updated package configuration and structure
- Removed deprecated setup.py in favor of pyproject.toml

### Added
- Comprehensive CHANGELOG.md following Keep a Changelog format
- Enhanced project structure documentation
- Improved package metadata

### Fixed
- Directory structure inconsistencies
- Package configuration organization

## [0.3.1] - 2024-10-08

### Added
- Bilingual README (English and Spanish)

### Changed
- Updated API reference documentation to include detailed information about Cheques and Estadísticas Cambiarias modules
- Enhanced usage guide with examples for all modules
- Revised main documentation page to reflect the full range of features

### Fixed
- Corrected inconsistencies in documentation
- Improved clarity and readability throughout the documentation

## [0.3.0] - 2024-10-07

### Added
- New Cheques module for interacting with the BCRA Cheques API
- New Estadísticas Cambiarias module for currency exchange rate data
- Comprehensive type hinting for all modules
- Extensive unit tests for new and existing modules

### Changed
- Improved error handling and response parsing for all API endpoints
- Enhanced code organization and modularity
- Updated API reference documentation to include new modules and endpoints

### Fixed
- Various minor bug fixes and improvements

## [0.2.0] - 2024-09-07

### Added
- Comprehensive revision of all documentation files
- Expanded installation guide
- New contributing guidelines
- Enhanced API reference documentation

### Changed
- Revised Read the Docs configuration for better documentation building
- Updated project metadata and version information

### Fixed
- Corrected inconsistencies in version numbering
- Fixed links and references in documentation files

## [0.1.1] - 2024-08-29

### Security
- Updated `requests` to version 2.32.0 or higher
- Addressed potential SSL verification issue

### Changed
- Updated `matplotlib` to version 3.7.3 or higher
- Updated `setuptools` to version 70.0.0 or higher
- Updated `urllib3` to version 2.2.1 or higher

## [0.1.0] - 2024-08-25

### Added
- Initial release of the BCRA API Connector
- `BCRAConnector` class for interacting with the BCRA API
- Principal variables functionality (`get_principales_variables`)
- Historical data retrieval (`get_datos_variable`)
- Latest value fetching (`get_latest_value`)
- Custom exception `BCRAApiError` for error handling
- Retry logic with exponential backoff
- SSL verification toggle
- Debug mode for detailed logging

### Requirements
- Python 3.9 or higher

### Documentation
- Initial README with project overview
- Comprehensive API documentation
- Usage examples for all main features
- Installation guide

[0.4.1]: https://github.com/PPeitsch/bcra-connector/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/PPeitsch/bcra-connector/compare/v0.3.3...v0.4.0
[0.3.3]: https://github.com/PPeitsch/bcra-connector/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/PPeitsch/bcra-connector/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/PPeitsch/bcra-connector/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/PPeitsch/bcra-connector/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/PPeitsch/bcra-connector/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/PPeitsch/bcra-connector/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/PPeitsch/bcra-connector/releases/tag/v0.1.0