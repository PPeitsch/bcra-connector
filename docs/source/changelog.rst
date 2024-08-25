# Changelog

All notable changes to the BCRA API Connector will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-08-25

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

### Examples
- Scripts demonstrating various use cases:
  - Fetching and visualizing principal variables
  - Retrieving and plotting historical data
  - Comparing latest values for multiple variables
  - Error handling scenarios
  - Different connector configurations

### Development
- Project structure set up for future expansion
- Basic error handling and logging implemented
- Foundation laid for future testing framework

[0.1.0]: https://github.com/yourusername/bcra-api-connector/releases/tag/v0.1.0
