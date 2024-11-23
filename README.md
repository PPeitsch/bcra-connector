# BCRA API Connector

[![PyPI version](https://badge.fury.io/py/bcra-connector.svg)](https://badge.fury.io/py/bcra-connector)
[![Python Versions](https://img.shields.io/pypi/pyversions/bcra-connector.svg)](https://pypi.org/project/bcra-connector/)
[![Documentation Status](https://readthedocs.org/projects/bcra-connector/badge/?version=latest)](https://bcra-connector.readthedocs.io/en/latest/?badge=latest)
[![Coverage](https://codecov.io/gh/PPeitsch/bcra-connector/branch/main/graph/badge.svg)](https://codecov.io/gh/PPeitsch/bcra-connector)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/PPeitsch/bcra-connector/workflows/Test%20and%20Publish/badge.svg)](https://github.com/PPeitsch/bcra-connector/actions/workflows/test-and-publish.yaml)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](.github/CODE_OF_CONDUCT.md)

A Python connector for the BCRA (Banco Central de la República Argentina) APIs, including Estadísticas v2.0, Cheques, and Estadísticas Cambiarias.

## Features

- Fetch principal variables published by BCRA
- Retrieve historical data for specific variables
- Get the latest value for a variable
- Access information about reported checks
- Retrieve currency exchange rate data
- Bilingual support (Spanish and English)
- Error handling with custom exceptions
- Retry logic with exponential backoff
- SSL verification (optional)
- Debug mode for detailed logging

## Documentation

Full documentation, including installation instructions, usage examples, and API reference, is available at:
- [Read the Docs Documentation](https://bcra-connector.readthedocs.io/)
- [Quick Start Guide](https://bcra-connector.readthedocs.io/en/latest/usage.html)
- [API Reference](https://bcra-connector.readthedocs.io/en/latest/api_reference.html)

## Installation

```bash
pip install bcra-connector
```

For detailed installation instructions and requirements, see our [Installation Guide](https://bcra-connector.readthedocs.io/en/latest/installation.html).

## Contributing

Contributions are welcome! Please read our:
- [Contributing Guidelines](.github/CONTRIBUTING.md)
- [Code of Conduct](.github/CODE_OF_CONDUCT.md)

## Security

For vulnerability reports, please review our [Security Policy](.github/SECURITY.md).

## Change Log

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version updates.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This project is not officially affiliated with or endorsed by the Banco Central de la República Argentina. Use at your own risk.