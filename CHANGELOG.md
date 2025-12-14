# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.1] - 2025-12-14

### Added

- Unit tests for `to_dataframe()` methods to improve coverage (#80)
- `pandas` and `pandas-stubs` to pre-commit mypy environment (#80)

### Changed

- Removed unused `pandas` from mypy `ignore_missing_imports` (#80)

## [0.8.0] - 2025-12-10

### Added

- `to_dataframe()` method to `PrincipalesVariables` model for pandas DataFrame conversion (#79)
- `to_dataframe()` method to `DetalleMonetaria` and `DatosVariable` models (#79)
- `to_dataframe()` method to `Entidad` and `Cheque` models (#79)
- `to_dataframe()` method to `CotizacionFecha` model (#79)
- Optional `pandas` dependency: `pip install bcra-connector[pandas]` (#79)

### Changed

- Added `pandas` to mypy `ignore_missing_imports` configuration (#79)

## [0.7.2] - 2025-12-10

### Added

- `AGENT.md` with project context for AI assistants (#78)
- `myst_parser` integration for including `CHANGELOG.md` in ReadTheDocs (#78)

### Changed

- `docs/source/conf.py` now imports version dynamically from `__about__.py` (single source of truth) (#78)
- Expanded PyPI keywords for better discoverability (`bcra-api`, `python-bcra`, `tipo-cambio`, etc.) (#78)
- Updated `AGENT_WORKFLOW.md` with note about automatic version synchronization (#78)

## [0.7.1] - 2025-12-10

### Fixed

- Updated `usage.rst` examples to use v4.0 API structure (`ultValorInformado`/`ultFechaInformada` instead of obsolete `valor`/`fecha`) (#76)
- Fixed `get_datos_variable()` example in documentation to handle `DatosVariableResponse` correctly (#76)
- Added missing 0.6.2 entry to `changelog.rst` (#76)
- Updated comparison links in `CHANGELOG.md` to include v0.7.0 (#76)

## [0.7.0] - 2025-12-09

### ⚠️ BREAKING CHANGES

- **Upgraded Principales Variables API from v3.0 to v4.0**
  - `get_latest_value()` now returns `DetalleMonetaria` (with `fecha` and `valor` fields) instead of `DatosVariable`
  - `get_variable_history()` now returns `List[DetalleMonetaria]` instead of `List[DatosVariable]`
  - `PrincipalesVariables` model updated with new v4.0 structure:
    - Removed direct `fecha` and `valor` fields
    - Added: `tipoSerie`, `periodicidad`, `unidadExpresion`, `moneda`
    - Added: `primerFechaInformada`, `ultFechaInformada`, `ultValorInformado`
  - `DatosVariable` now contains a list of `DetalleMonetaria` objects in `detalle` field
  - API endpoint changed: `estadisticas/v3.0/monetarias` → `estadisticas/v4.0/Monetarias`
  - Query parameters now capitalized: `Desde`, `Hasta`, `Limit`, `Offset`

### Added

- New `DetalleMonetaria` class for individual monetary data points (#75)
- Extended metadata fields in `PrincipalesVariables` model (#75)
- `status` field added to `DatosVariableResponse` for HTTP status tracking (#75)
- Comprehensive test coverage for KeyError edge cases in data models (#75)
- Coverage configuration in `pyproject.toml` to exclude auto-generated files (#75)
- Test for fallback scenario in `get_latest_value()` method (#75)

### Changed

- Updated all Principales Variables endpoints to v4.0 (#75)
- Capitalized query parameter names to match v4.0 API specification (#75)
- Enhanced `get_datos_variable()` to handle nested `detalle` arrays (#75)
- Improved `get_latest_value()` with 30-day fallback mechanism (#75)
- Updated `get_variable_history()` to return flattened list of data points (#75)
- Completely rewrote unit tests for v4.0 data model structure (#75)
- Updated integration tests to validate v4.0 API responses (#75)

### Fixed

- Type annotations added to `get_latest_value()` and `get_variable_history()` (#75)
- Improved error handling for missing keys in API responses (#75)

### Testing

- **100% code coverage** achieved (825/825 statements)
- 185 tests passing (4 new tests added)
- All integration tests validated against live v4.0 API
- MyPy type checking passing without errors

## [0.6.2] - 2025-12-08

### Fixed
- Corrected package name from `bcra-api-connector` to `bcra-connector` in installation documentation (#73).
- Added missing imports to code examples in `usage.rst` and `configuration.rst` so they can be copied and run directly.
- Updated `examples.rst` to include import statements by changing `:lines: 11-` to `:lines: 6-` for all example files.
- Fixed all example files to use `from bcra_connector import` instead of `from src.bcra_connector import`.
- Removed unnecessary `sys.path` manipulation from example files (users should use `pip install -e .` for development).
- Cleaned up unused imports (`sys`) from example files while keeping necessary ones (`os` for `save_plot()`).

## [0.6.1] - 2025-12-08

### Added
- Extended unit test suite achieving 100% coverage for `bcra_connector.py` and all models (#56).
- Comprehensive edge case testing for error handling, parsing, and validation.

### Changed
- Configured pytest to ignore `InsecureRequestWarning` from urllib3 in test output.

### Fixed
- Minor bugs exposed by extended test coverage in data model validation.

## [0.6.0] - 2025-12-08

### Added
- Documentation examples for `Cheques` and `Exchange Statistics` synced to ReadTheDocs.

### Changed
- Enforced strict CI/CD verification rules in Agent Workflow.

### Fixed
- Trailing whitespace in documentation files.
- Consistency between `CHANGELOG.md` and `docs/source/changelog.rst`.

## [0.5.4] - 2025-12-08

### Added
- Example scripts for `Cheques` and `Estadísticas Cambiarias` API usage (#57).
- Module-level docstrings for all subpackages (#55).

### Fixed
- Linting and type errors in example scripts.

## [0.5.3] - 2025-12-08

### Added
- Automated GitHub Release creation from CHANGELOG upon pushing tags.
- Quick Start section to README.md with code examples.
- Enhanced Features list in README.md.

### Fixed
- Trailing whitespace issues in documentation.

## [0.5.2] - 2025-11-28

### Security
- Updated `setuptools` to `>=78.1.1` to address path traversal vulnerability (GHSA-r9hx-vwmv-q579) in deprecated `PackageIndex.download` function.

## [0.5.1] - 2025-11-28

### Fixed
- Relaxed `scipy` version constraint to `scipy>=1.13.1,<1.15.0` to support Python 3.9 environments.
- Updated mypy `python_version` configuration to `3.10` to support pattern matching syntax used by pytest.

## [0.5.0] - 2025-05-09

### Changed
- Migrated "Principales Variables" functionality to BCRA's "Estadísticas Monetarias v3.0" API.
    - `PrincipalesVariables` model: `cdSerie` removed, `categoria` added.
    - `get_datos_variable` method:
        - Now uses query parameters for dates, `limit`, and `offset`.
        - Returns `DatosVariableResponse` object (includes `metadata` and `results` list).
        - Client-side 1-year date range restriction removed (API uses pagination).
- Updated helper methods (`get_latest_value`, `get_variable_history`, etc.) for v3.0 API compatibility.

### Added
- `DatosVariableResponse` model for new API structure of historical data.

### Fixed
- MyPy type errors, unreachable code warnings, and module attribute resolution.
- Corrected `scipy.stats.pearsonr` import.
- Improved assertions in unit and integration tests for error handling.

### Updated
- Example scripts to demonstrate usage of Monetarias v3.0 API and new response types.
- Unit and integration tests to cover v3.0 API changes and new models.

## [0.4.2] - 2025-05-08

### Added
- Pre-commit configuration with `.pre-commit-config.yaml`
- Code quality hooks for automated checks:
  - Standard checks (whitespace, EOF, syntax validation)
  - Python code formatting with `black`
  - Import sorting with `isort`
  - Linting with `flake8`
  - Static type checking with `mypy`
- Root conftest.py to resolve module import issues for tests

### Enhanced
- Code formatting and style consistency across the codebase
- Type annotations and static type checking configuration
- Build system with improved version management
- CI/CD integration with local development workflow

### Fixed
- Matplotlib plot type errors with simplified date conversion
- Removed unreachable code in example files
- Eliminated unnecessary type ignore comments
- MyPy configuration for proper handling of src package structure
- Module-specific overrides for external dependencies

### Changed
- Removed auto-generated `_version.py` from version control
- Established `__about__.py` as the single source of truth for versioning
- Updated Sphinx version to resolve dependency conflicts with sphinx-rtd-theme

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


[0.8.1]: https://github.com/PPeitsch/bcra-connector/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/PPeitsch/bcra-connector/compare/v0.7.2...v0.8.0
[0.7.2]: https://github.com/PPeitsch/bcra-connector/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/PPeitsch/bcra-connector/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/PPeitsch/bcra-connector/compare/v0.6.2...v0.7.0
[0.6.2]: https://github.com/PPeitsch/bcra-connector/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/PPeitsch/bcra-connector/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/PPeitsch/bcra-connector/compare/v0.5.4...v0.6.0
[0.5.4]: https://github.com/PPeitsch/bcra-connector/compare/v0.5.3...v0.5.4
[0.5.3]: https://github.com/PPeitsch/bcra-connector/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/PPeitsch/bcra-connector/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/PPeitsch/bcra-connector/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/PPeitsch/bcra-connector/compare/v0.4.2...v0.5.0
[0.4.2]: https://github.com/PPeitsch/bcra-connector/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/PPeitsch/bcra-connector/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/PPeitsch/bcra-connector/compare/v0.3.3...v0.4.0
[0.3.3]: https://github.com/PPeitsch/bcra-connector/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/PPeitsch/bcra-connector/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/PPeitsch/bcra-connector/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/PPeitsch/bcra-connector/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/PPeitsch/bcra-connector/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/PPeitsch/bcra-connector/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/PPeitsch/bcra-connector/releases/tag/v0.1.0
