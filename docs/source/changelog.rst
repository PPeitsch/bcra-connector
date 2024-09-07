Changelog
=========

All notable changes to the BCRA API Connector will be documented in this file.

0.2.0 - 2024-09-20
------------------

Added
^^^^^
* Comprehensive documentation with usage examples and API reference
* Debug mode for detailed logging

Changed
^^^^^^^
* Improved error handling with custom ``BCRAApiError`` exception
* Enhanced retry logic with exponential backoff
* Improved documentation clarity and structure
* Updated README with more comprehensive information

Fixed
^^^^^
* SSL verification issues in certain environments

0.1.1 - 2024-08-29
------------------

Changed
^^^^^^^
* Updated dependencies to address security vulnerabilities

0.1.0 - 2024-08-23
------------------

Added
^^^^^
* Initial release of the BCRA API Connector
* ``BCRAConnector`` class for interacting with the BCRA API
* Methods to fetch principal variables (``get_principales_variables()``)
* Historical data retrieval (``get_datos_variable()``)
* Basic error handling and logging
* SSL verification toggle
* Bilingual support (Spanish and English)

Requirements
^^^^^^^^^^^^
* Python 3.9 or higher
* ``requests`` library for HTTP requests

Documentation
^^^^^^^^^^^^^
* README with project overview and basic usage
* Basic API documentation
* Installation guide
