# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Added
- The Monetarias models are snake_case like the rest of the library:
  `PrincipalesVariables.id_variable`, `.tipo_serie`, `.unidad_expresion`,
  `.primer_fecha_informada`, `.ult_fecha_informada`, `.ult_valor_informado` and
  `DatosVariable.id_variable`. The API's camelCase names still work — both when
  reading an attribute and when constructing a model — with a `DeprecationWarning`
  naming the replacement, until 1.0. `from_dict()`/`to_dict()` are unchanged: that is
  the API's own wire format (#135)
- Every date parameter accepts a `date`, a `datetime` or an ISO 8601 string, and the
  three are interchangeable: `monetarias.series(desde=...)` no longer demands a
  `datetime`, and `cambiarias.quotations()` / `.series()` no longer demand a string. A
  malformed string now raises a `ValueError` naming the parameter instead of reaching
  the API as an opaque error. The exported `DateLike` type spells this out (#133)
- `Page[T]`: every endpoint that returns several rows now answers with a page that
  carries the API's own `count`, `offset`, `limit` and `has_more` alongside the results.
  It behaves like the list it replaces — iteration, `len()`, indexing, slicing and `==`
  against a list all work — and it converts itself with `to_dict()` and
  `to_dataframe()`, which removes the `pd.DataFrame([x.to_dict() for x in ...])` recipe
  for lists (#131)
- Estadísticas Cambiarias now has its own client: `connector.cambiarias.currencies()`,
  `.quotations()`, `.latest()`, `.series()`, `.evolution()` and `.pair()` (#129)
- Monetarias now has its own client: `connector.monetarias.list()`, `.series()`,
  `.latest()`, `.find()` and `.history()` (#126)
- Cheques now has its own client: `connector.cheques.entities()`, `.reported()` and
  `.is_reported()`. `find_entity()` resolves an entity name (accent-insensitive, exact
  match first, then a unique substring) without making a request (#123)
- Central de Deudores now has its own client: `connector.deudores.debts()`,
  `.historical()` and `.rejected_checks()`. It accepts a CUIT with dashes, and the
  shared parsing helper reports which endpoint failed to parse (#121)
- `BCRAConnector(session=...)` accepts a `requests.Session`, for custom adapters,
  proxies or tests. The caller keeps ownership: `close()` leaves an injected session
  open and still closes one the connector created (#119)

### Deprecated
- The camelCase field names of `PrincipalesVariables` and `DatosVariable`
  (`idVariable`, `tipoSerie`, `unidadExpresion`, `primerFechaInformada`,
  `ultFechaInformada`, `ultValorInformado`) are deprecated in favour of their
  snake_case equivalents and will be removed in 1.0 (#135)
- The `*Response` models (`DatosVariableResponse`, `DivisaResponse`, `EntidadResponse`,
  `CotizacionResponse`, `CotizacionesResponse`, `ChequeResponse`) are superseded by
  `Page` and will be removed in 1.0. The deprecated `get_*` methods still return the old
  types, so code on 0.12 is unaffected (#131)
- `get_divisas()`, `get_cotizaciones()`, `get_evolucion_moneda()`,
  `get_currency_evolution()`, `get_latest_quotations()` and
  `get_currency_pair_evolution()` are deprecated in favour of `connector.cambiarias.*`
  and will be removed in 1.0 (#129)
- `get_principales_variables()`, `get_datos_variable()`, `get_latest_value()`,
  `get_variable_by_name()` and `get_variable_history()` are deprecated in favour of
  `connector.monetarias.*` and will be removed in 1.0 (#126)
- `get_entidades()`, `get_cheque_denunciado()` and `check_denunciado()` are deprecated
  in favour of `connector.cheques.*` and will be removed in 1.0 (#123)
- `get_deudas()`, `get_deudas_historicas()` and `get_cheques_rechazados()` are
  deprecated in favour of `connector.deudores.*` and will be removed in 1.0. They
  delegate and emit a `DeprecationWarning` naming the replacement (#121)

### Changed
- `DatosVariable` instances now compare every field. `__eq__` looked only at
  `idVariable`, so two series with the same id but different `detalle` — or an empty
  one — compared equal (#135)
- `cambiarias.pair()` reports `fecha` as a `date` instead of an ISO string, so every
  date the library returns is now a `date` (#133)
- Internal: the HTTP transport (session, retries, rate limiting, timeouts, pagination
  and the catalog cache) moved to an internal `HttpClient`; `BCRAConnector` delegates to
  it. No public behavior changes — `BASE_URL`, `MAX_RETRIES`, `RETRY_DELAY`,
  `MAX_PAGE_SIZE`, `FX_MAX_PAGE_SIZE`, `MAX_PAGES` and `CATALOG_CACHE_TTL` remain class
  attributes and are read on every call, so subclassing or assigning them keeps
  working (#119)
- Internal: `CLAUDE.md` is now a one-line `@AGENTS.md` import instead of a prose
  pointer, so the canonical instructions load automatically; the redundant `AGENT.md`
  compatibility stub was removed. `AGENTS.md` dropped the descriptive project overview,
  the hand-written directory tree (already stale — it predated `clients/` and `_http.py`)
  and the skills table that duplicated `AGENT_MANIFEST.md`; every rule stays inline

### Added
- `docs` extra with the documentation dependencies (`sphinx`, `sphinx-rtd-theme`,
  `myst-parser`), so `pip install -e ".[docs]"` is enough to build the docs locally.
  `docs/requirements.txt` and `.readthedocs.yaml` now point at it instead of keeping a
  second list (#115)

### Changed
- `pre-commit` hooks updated (`pre-commit-hooks` v6.0.0, `black` 26.5.1, `isort` 9.0.1,
  `flake8` 7.3.0, `mypy` v2.3.1), which removes the deprecated stage-name warnings. The
  mypy hook now pins the newest pandas/numpy that still support Python 3.10, the
  project's minimum: pandas 3 and pandas-stubs 3 require 3.11+, and mypy silently typed
  their `DataFrame` as `Any` (#115)

### Fixed
- Documentation: the examples page embedded three images that returned 404 in the
  published docs. They are produced by running the examples, which write them to the
  gitignored `docs/build/`, so Read the Docs never had them (#117)
- Documentation: the installation guide listed `matplotlib` and `setuptools` as runtime
  dependencies and an outdated `requests` range, and linked to a `troubleshooting` page
  that doesn't exist (#115)

## [0.12.0] - 2026-09-19

### Added
- Python 3.12 and 3.13 are tested in CI and listed in the package classifiers (#105)
- Typed exceptions, all subclasses of `BCRAApiError` so existing handlers keep working:
  `BCRANotFoundError` (HTTP 404), `BCRARateLimitError` (429 after retries) and
  `BCRAServerError` (5xx after retries). Every `BCRAApiError` has a `status_code`
  attribute (`None` when there was no HTTP response) (#107)
- `check_denunciado()` resolves the entity ignoring case and accents, and accepts a
  unique part of the name (`"Santander"`, `"Banco de la Nación Argentina"`). If several
  entities match, it raises `ValueError` listing them (#107)
- `verify_ssl` also accepts the path to a CA bundle (`str` or `os.PathLike`), as
  `requests` does, for proxies that inspect TLS; a missing file raises `ValueError` at
  construction. `close()` releases the HTTP session, and `BCRAConnector` works as a
  context manager (#113)

### Changed
- `get_currency_pair_evolution(base, quote)` now returns the amount of **quote** for
  one unit of **base**, the usual `BASE/QUOTE` convention. It used to return the
  inverse: `("USD", "EUR")` gave ~1.16 (dollars per euro) and now gives ~0.87 (euros per
  dollar). Rates are computed through the dollar with `tipoPase`, so ARS, gold (XAU)
  and silver (XAG), which have no `tipoCotizacion`, now work instead of returning
  `0.0` (`("USD", "ARS")` is the official peso quotation). Pairs against USD make one
  request instead of two, and currency codes are case-insensitive (#109)
- `check_denunciado()` no longer returns `False` on an HTTP 404. The Cheques API answers
  a check that isn't reported with `200` and `denunciado: false`; its only 404 is
  "Entidad informada inexistente", which now propagates as `BCRANotFoundError`. It also
  stopped matching `"404"`/`"not found"` in error messages (#107)
- A plain `pytest` run no longer includes the integration tests, which call the live
  BCRA API; run them with `pytest -m integration`. In CI they moved to a separate
  workflow (manual and weekly) that doesn't gate pull requests, and they now verify SSL.
  CI actions were bumped to their current majors, and the mypy pre-commit hook pins its
  dependencies (#105)
- `numpy` and `scipy` are no longer required dependencies. `scipy` is dropped
  (`get_variable_correlation()` now uses `numpy.corrcoef`), and `numpy` moves to the new
  `[analytics]` extra with no upper pin, so the connector installs on Python 3.13 and
  alongside numpy 2. `generate_variable_report()` uses the standard library `statistics`
  module and works without numpy. `get_variable_correlation()` raises `ImportError`
  asking for `pip install "bcra-connector[analytics]"` when numpy is missing (#103)
- The `User-Agent` header is now `bcra-connector/<version>` instead of the fixed
  `BCRAConnector/1.0` (#113)

### Fixed
- Documentation (#111): the docs index listed "Estadísticas v2.0" instead of Monetarias
  v4.0 and omitted Central de Deudores; two docstrings said "Monetarias v3.0"; the
  logging section predated the library-friendly logging of 0.11.0; the README Quick
  Start had an empty step; and the usage guide called `to_dataframe()` on a list
  (`AttributeError`) and labelled the 5 oldest points of a series as the latest

## [0.11.0] - 2026-09-19

### Added
- Name lookups reuse the variables catalog and the cheque entities list for
  `CATALOG_CACHE_TTL` seconds (default 300, `0` disables it); `clear_cache()` forces a
  refetch. `generate_variable_report()` no longer downloads the 1610-series catalog
  twice, and repeated name-based calls or `check_denunciado()` calls don't download it
  again. `get_principales_variables()` and `get_entidades()` remain uncached (#101)

### Changed
- The library no longer configures logging. The `bcra_connector` package logger gets a
  `NullHandler`, and `BCRAConnector` no longer attaches a `StreamHandler` or forces the
  level to `INFO`, so nothing is printed unless the application configures logging.
  `debug=True` remains an explicit opt-in: it sets `DEBUG` and adds a stderr handler
  only if no other handler would receive the records (#95)

### Fixed
- `generate_variable_report()` returned `start_date`/`end_date`, `latest_value` and
  `percent_change` reversed: the Monetarias v4.0 API returns series newest-first and the
  report assumed ascending order. The data is now sorted by date before computing (#93)
- `get_variable_by_name()` swallowed `BCRAApiError` and returned `None`, so
  `get_variable_history()`, `generate_variable_report()` and
  `get_variable_correlation()` reported an API failure as "Variable not found". The
  error now propagates, as those methods already documented (#97)
- `get_variable_by_name()` now prefers an exact (case-insensitive) description match,
  and logs a warning listing the candidates when several series match only by
  substring. It still returns the first match, so the return value is unchanged in
  the ambiguous case (#97)
- Results were silently truncated at the APIs' default of 1000 (#99):
  - `get_principales_variables()` returned 1000 of the 1610 series in the catalog, so
    `get_variable_by_name()` could not find the rest. It now pages through the catalog.
  - `get_variable_history()` without `limit`/`offset` now returns the whole date range,
    fetching as many pages as needed. An explicit `limit`/`offset` still means a single
    page.
  - `get_currency_evolution()` returned at most 1000 dates. Its `limit` now defaults to
    `None`, meaning the whole range; passing `limit` keeps single-page behaviour.
  - `get_currency_pair_evolution()` raised `ValueError` for `days > 985` (it requested
    `limit=days+15`, above the API maximum). It now uses the full range.
  - `get_evolucion_moneda()` logs a warning when its page does not cover all results.

### Security
- Central de Deudores methods no longer log the queried CUIT/CUIL/CDI or the person's
  name, and 11-digit identifiers are masked in the URLs logged by retries and debug
  output (#95)

## [0.10.0] - 2026-09-18

### Removed
- **Python 3.9 support.** `requires-python` is now `>=3.10`. Python 3.9 reached
  end-of-life in October 2025, and the patched `requests` release below does not
  install on it (#91)
- `requirements.txt`, which duplicated `pyproject.toml` and had already diverged from
  it (it listed `matplotlib` and `setuptools` as runtime dependencies).
  `pyproject.toml` is the single source of truth; use `pip install -e ".[dev]"` (#91)

### Security
- Require `requests>=2.33.0` to fix
  [GHSA-gc5v-m9x4-r6x2](https://github.com/advisories/GHSA-gc5v-m9x4-r6x2), insecure
  temp file reuse in `extract_zipped_paths()`. The previous `<2.33.0` cap made the
  patched release uninstallable (#91)

## [0.9.4] - 2026-09-17

### Changed
- `_make_request()` now retries transient `429` and `5xx` responses with the same
  exponential backoff already used for timeouts and connection errors, raising
  `BCRAApiError` only after `MAX_RETRIES` attempts (#86)

### Fixed
- DataFrame tests imported `pandas` directly, so they errored instead of skipping
  when the optional `[pandas]` extra was not installed (#86)

## [0.9.3] - 2026-09-17

### Added
- `.gitignore` entries for the local agent workspace directories `_ref/`, `_wip/`
  and `_done/` (#87)

### Changed
- Restructured agent documentation around a canonical `AGENTS.md` following the
  [agents.md](https://agents.md) convention. `CLAUDE.md` and `AGENT.md` are now thin
  pointers to it, so no entry point can dangle (#89)
- Rewrote `WORKFLOW.md` for Linux/bash, replacing the incorrect Windows/PowerShell
  environment and snippets (#89)
- Reconciled the documented commit format with the repository's actual history
  (`[type]: Description`, lowercase with colon) (#89)

### Fixed
- `get_latest_value()` 30-day fallback reused `metadata.resultset.limit` from the
  preceding `limit=10` request, capping the fallback query at 10 results instead of
  covering a month of daily data (#85)
- `examples/02_get_datos_variable.py` used `Axes.plot_date`, which matplotlib removed
  from its type stubs, breaking the Code Quality job (#85)
- `.gitignore` had an entry appended as UTF-16LE, embedding NUL bytes mid-file so git
  never matched the pattern and `central-deudores-v1.pdf` was not actually ignored
  (#87)
- `CLAUDE.md` instructed agents to read `AGENTS.md`, which did not exist (the file was
  `AGENT.md`), so a literal read failed (#89)
- `WORKFLOW.md`, which holds the mandatory SOP, was not reachable from the documented
  entry point and is now linked prominently (#89)
- Documented the `.skills/` submodule bootstrap; without it every
  `.agent/workflows/*.md` command fails (#89)
- Documented that branches must be deleted on merge: leaving a base branch alive
  prevents GitHub from re-targeting stacked PRs, which then receive no CI (#89)

## [0.9.2] - 2026-03-04

### Changed
- Added .skills submodule
- Updated agent configuration, workflows, and AGENT.md

### Fixed
- Improved connector error handling for HTTP 5xx responses and expanded unit tests

## [0.9.0] - 2025-12-17

### Added

- **Central de Deudores API (v1.0)**: Full support for BCRA's Debtor Registry (#81)
  - New dataclasses: `EntidadDeuda`, `Periodo`, `Deudor`, `ChequeRechazado`, `EntidadCheques`, `CausalCheques`, `ChequesRechazados`
  - `get_deudas(identificacion)`: Query current debts by CUIT/CUIL/CDI
  - `get_deudas_historicas(identificacion)`: Query historical debts (24 months)
  - `get_cheques_rechazados(identificacion)`: Query rejected checks with causals
  - `to_dataframe()` support for all new models
- Example script `08_central_deudores.py` demonstrating API usage (#81)
- Unit tests for Central de Deudores models and connector methods (#81)

### Changed

- Updated README with Central de Deudores feature and DataFrame support documentation (#81, #82)
- Renamed agent docs: `AGENT.md` → `AGENTS.md`, moved `AGENT_WORKFLOW.md` → `WORKFLOW.md`

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


[0.12.0]: https://github.com/PPeitsch/bcra-connector/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/PPeitsch/bcra-connector/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/PPeitsch/bcra-connector/compare/v0.9.4...v0.10.0
[0.9.4]: https://github.com/PPeitsch/bcra-connector/compare/v0.9.3...v0.9.4
[0.9.3]: https://github.com/PPeitsch/bcra-connector/compare/v0.9.2...v0.9.3
[0.9.2]: https://github.com/PPeitsch/bcra-connector/compare/v0.9.0...v0.9.2
[0.9.0]: https://github.com/PPeitsch/bcra-connector/compare/v0.8.1...v0.9.0
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
