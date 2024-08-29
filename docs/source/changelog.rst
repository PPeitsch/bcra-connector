# Changelog

All notable changes to the BCRA API Connector will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2024-08-29

### Changed
- Updated `requests` to version 2.32.0 or higher to address a security vulnerability related to SSL verification
- Updated `matplotlib` to version 3.7.3 or higher for improved compatibility
- Updated `setuptools` to version 70.0.0 or higher
- Updated `urllib3` to version 2.2.1 or higher

### Fixed
- Addressed potential SSL verification issue with `requests` library, improving overall security

### Notes
- This release focuses on security enhancements and dependency upgrades. All users are encouraged to update to this version.

## [0.1.0] - 2024-08-23

### Added
- Initial release of the BCRA API Connector
- `BCRAConnector` class for interacting with the BCRA API
- Functionality to fetch principal variables (`get_principales_variables`)
- Historical data retrieval (`get_datos_variable`)
- Latest value fetching (`get_latest_value`)
- Custom exception `BCRAApiError` for error handling
- Retry logic with exponential backoff
- SSL verification toggle
- Debug mode for detailed logging

### Requirements
- Python 3.9 or higher

### Documentation
- README with project overview and basic usage
- Comprehensive API documentation
- Usage examples for all main features
- Installation guide

### Development
- Project structure set up for future expansion
- Basic error handling and logging implemented
- Foundation laid for future testing framework

[0.1.1]: https://github.com/PPeitsch/bcra-connector/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/PPeitsch/bcra-connector/releases/tag/v0.1.0
