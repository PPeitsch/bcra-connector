# BCRA API Connector

[![PyPI version](https://badge.fury.io/py/bcra-connector.svg)](https://badge.fury.io/py/bcra-connector)
[![Python Versions](https://img.shields.io/pypi/pyversions/bcra-connector.svg)](https://pypi.org/project/bcra-connector/)
[![Documentation Status](https://readthedocs.org/projects/bcra-connector/badge/?version=latest)](https://bcra-connector.readthedocs.io/en/latest/?badge=latest)
[![Coverage](https://codecov.io/gh/PPeitsch/bcra-connector/branch/main/graph/badge.svg)](https://codecov.io/gh/PPeitsch/bcra-connector)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/PPeitsch/bcra-connector/workflows/Test%20and%20Publish/badge.svg)](https://github.com/PPeitsch/bcra-connector/actions/workflows/test-and-publish.yaml)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](.github/CODE_OF_CONDUCT.md)

A Python connector for the BCRA (Banco Central de la República Argentina) APIs, covering Principal Variables/Monetary Statistics, Cheques, and Exchange Rate Statistics.

## Features

- **Comprehensive Data Access**: Fetch Principal Variables, Monetary Statistics, Checks information, and Exchange Rates.
- **Historical Data**: Easily retrieve and analyze historical time series for any variable.
- **Robustness**: Built-in retry logic with exponential backoff and safe failure handling.
- **Developer Friendly**:
  - Full **Type Hinting** for better IDE support.
  - Bilingual context (Spanish API / English Wrapper).
  - Detailed debug logging.
- **Configurable**: Options for SSL verification, retries, and timeouts.

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

## Quick Start

Get up and running in seconds:

```python
from bcra_connector import BCRAConnector

# Initialize the connector
connector = BCRAConnector()

# 1. List principal variables published by BCRA
variables = connector.get_principales_variables()
print(f"Found {len(variables)} variables.")

# 2. Get the latest value for a specific variable (e.g., using the ID of the first one)
if variables:
    target_var = variables[0]
    print(f"Fetching data for: {target_var.descripcion} (ID: {target_var.idVariable})")

    latest = connector.get_latest_value(target_var.idVariable)
    print(f"Latest Value: {latest.valor} on {latest.fecha}")

# 3. Get historical data (last 30 days)
#    (Note: Date range filtering is handled by the API or post-processing)
```

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
