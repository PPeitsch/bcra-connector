Changelog
=========

All notable changes to the BCRA API Connector will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

0.4.1 - 2024-12-28
------------------

Added
^^^^^
* Comprehensive unit test coverage for all major components
* Extensive integration tests for BCRA API endpoints
* Complete test suite for rate limiter and error handling
* Improved type annotations across test infrastructure
* Detailed test cases for data models and edge cases

Enhanced
^^^^^^^^
* Test coverage for principales_variables, cheques, and estadisticas_cambiarias modules
* Error handling and rate limiting test scenarios
* Reliability of rate limiter implementation
* Consistency in test suite structure and methodology

Fixed
^^^^^
* Intermittent test failures in rate limiting tests
* SSL and timeout error handling test coverage
* Type annotation issues in test files
* Flaky test behaviors in CI environment

Changed
^^^^^^^
* Improved test suite organization
* Enhanced error message validation
* Refined rate limiter state tracking logic

0.4.0 - 2024-11-23
------------------

Added
^^^^^
* Contributor Covenant Code of Conduct
* Structured issue templates
* Security policy document
* Pull request template
* GitHub Actions workflow for testing and publishing
* Comprehensive community guidelines
* Automated testing and publishing process

Enhanced
^^^^^^^^
* Updated README with new badges and improved organization
* Improved contributing guidelines with clear standards
* Enhanced example scripts documentation
* Better error handling and logging
* Project structure and organization
* Documentation system
* Streamlined contribution process

Fixed
^^^^^
* CI/CD badge display in README
* Documentation inconsistencies
* Build process reliability
* Version tracking system

0.3.1 - 2024-10-08
------------------

Added
^^^^^
* Bilingual README (English and Spanish)

Changed
^^^^^^^
* Updated API reference documentation to include detailed information about Cheques and Estadísticas Cambiarias modules
* Enhanced usage guide with examples for all modules
* Revised main documentation page to reflect the full range of features

Fixed
^^^^^
* Corrected inconsistencies in documentation
* Improved clarity and readability throughout the documentation

0.3.0 - 2024-10-07
------------------

Changed
^^^^^^^
* Updated API reference documentation to include Cheques and Estadísticas Cambiarias modules
* Enhanced usage guide with examples for new modules
* Revised main documentation page to reflect the full range of features

Fixed
^^^^^
* Corrected inconsistencies in documentation
* Improved clarity and readability throughout the documentation

0.3.0 - 2024-10-07
------------------

Added
^^^^^
* New Cheques module for interacting with the BCRA Cheques API
* New Estadísticas Cambiarias module for currency exchange rate data
* Comprehensive type hinting for all modules
* Extensive unit tests for new and existing modules

Changed
^^^^^^^
* Improved error handling and response parsing for all API endpoints
* Enhanced code organization and modularity
* Updated API reference documentation to include new modules and endpoints

Fixed
^^^^^
* Various minor bug fixes and improvements

0.2.0 - 2024-09-07
------------------

Added
^^^^^
* Comprehensive revision of all documentation files for improved clarity and readability
* Expanded installation guide covering various installation methods
* Updated and improved usage examples
* New contributing guidelines to encourage community participation
* Enhanced API reference documentation with more detailed descriptions

Changed
^^^^^^^
* Revised Read the Docs configuration for better documentation building
* Updated project metadata and version information

Fixed
^^^^^
* Corrected inconsistencies in version numbering across project files
* Fixed links and references in documentation files

0.1.1 - 2024-08-29
------------------

Security
^^^^^^^^
* Updated ``requests`` to version 2.32.0 or higher to address a security vulnerability
* Addressed potential SSL verification issue with the ``requests`` library

Changed
^^^^^^^
* Updated ``matplotlib`` to version 3.7.3 or higher
* Updated ``setuptools`` to version 70.0.0 or higher
* Updated ``urllib3`` to version 2.2.1 or higher

0.1.0 - 2024-08-25
------------------

Added
^^^^^
* Initial release of the BCRA API Connector
* ``BCRAConnector`` class for interacting with the BCRA API
* Functionality to fetch principal variables (``get_principales_variables``)
* Historical data retrieval (``get_datos_variable``)
* Latest value fetching (``get_latest_value``)
* Custom exception ``BCRAApiError`` for error handling
* Retry logic with exponential backoff
* SSL verification toggle
* Debug mode for detailed logging

Requirements
^^^^^^^^^^^^
* Python 3.9 or higher

Documentation
^^^^^^^^^^^^^
* README with project overview and basic usage
* Comprehensive API documentation
* Usage examples for all main features
* Installation guide

Examples
^^^^^^^^
* Scripts demonstrating various use cases:
    * Fetching and visualizing principal variables
    * Retrieving and plotting historical data
    * Comparing latest values for multiple variables
    * Error handling scenarios
    * Different connector configurations

Development
^^^^^^^^^^^
* Project structure set up for future expansion
* Basic error handling and logging implemented
* Foundation laid for future testing framework