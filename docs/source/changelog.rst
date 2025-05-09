Changelog
=========

All notable changes to the BCRA API Connector will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

0.5.0 - 2025-05-09
------------------

Changed
^^^^^
* Migrated "Principales Variables" functionality to BCRA's "Estadísticas Monetarias v3.0" API.
    - `PrincipalesVariables` model: `cdSerie` removed, `categoria` added.
    - `get_datos_variable` method:
        - Now uses query parameters for dates, `limit`, and `offset`.
        - Returns `DatosVariableResponse` object (includes `metadata` and `results` list).
        - Client-side 1-year date range restriction removed (API uses pagination).
* Updated helper methods (`get_latest_value`, `get_variable_history`, etc.) for v3.0 API compatibility.

Added
^^^^^
* `DatosVariableResponse` model for new API structure of historical data.

Fixed
^^^^^
* MyPy type errors, unreachable code warnings, and module attribute resolution.
* Corrected `scipy.stats.pearsonr` import.
* Improved assertions in unit and integration tests for error handling.

Updated
^^^^^
* Example scripts to demonstrate usage of Monetarias v3.0 API and new response types.
* Unit and integration tests to cover v3.0 API changes and new models.

0.4.2 - 2025-05-08
------------------

Added
^^^^^
* Pre-commit configuration with ``.pre-commit-config.yaml``
* Code quality hooks for automated checks:
   - Standard checks (whitespace, EOF, syntax validation)
   - Python code formatting with ``black``
   - Import sorting with ``isort``
   - Linting with ``flake8``
   - Static type checking with ``mypy``
* Root conftest.py to resolve module import issues for tests

Enhanced
^^^^^^^^
* Code formatting and style consistency across the codebase
* Type annotations and static type checking configuration
* Build system with improved version management
* CI/CD integration with local development workflow

Fixed
^^^^^
* Matplotlib plot type errors with simplified date conversion
* Removed unreachable code in example files
* Eliminated unnecessary type ignore comments
* MyPy configuration for proper handling of src package structure
* Module-specific overrides for external dependencies

Changed
^^^^^^^
* Removed auto-generated ``_version.py`` from version control
* Established ``__about__.py`` as the single source of truth for versioning
* Updated Sphinx version to resolve dependency conflicts with sphinx-rtd-theme

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
