# BCRA API Connector

[![PyPI version](https://badge.fury.io/py/bcra-connector.svg)](https://badge.fury.io/py/bcra-connector)
[![Python Versions](https://img.shields.io/pypi/pyversions/bcra-connector.svg)](https://pypi.org/project/bcra-connector/)
[![Documentation Status](https://readthedocs.org/projects/bcra-connector/badge/?version=latest)](https://bcra-connector.readthedocs.io/en/latest/?badge=latest)
[![Coverage](https://codecov.io/gh/PPeitsch/bcra-connector/branch/main/graph/badge.svg)](https://codecov.io/gh/PPeitsch/bcra-connector)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/PPeitsch/bcra-connector/workflows/Test%20and%20Publish/badge.svg)](https://github.com/PPeitsch/bcra-connector/actions/workflows/test-and-publish.yaml)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](.github/CODE_OF_CONDUCT.md)

A Python connector for the BCRA (Banco Central de la República Argentina) APIs, covering Principal Variables/Monetary Statistics, Cheques, Exchange Rate Statistics, and Central de Deudores (Debtor Registry).

## Features

- **Comprehensive Data Access**: Fetch Principal Variables, Monetary Statistics, Checks information, Exchange Rates, and Debtor Registry data.
- **Central de Deudores**: Query debtor information, historical debts, and rejected checks by CUIT/CUIL.
- **DataFrame Support**: Convert API responses to pandas DataFrames with `to_dataframe()` methods.
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

# With pandas support for DataFrame conversion
pip install "bcra-connector[pandas]"

# With numpy, needed only by get_variable_correlation()
pip install "bcra-connector[analytics]"
```

For detailed installation instructions and requirements, see our [Installation Guide](https://bcra-connector.readthedocs.io/en/latest/installation.html).

## Quick Start

Get up and running in seconds:

```python
from bcra_connector import BCRAConnector

connector = BCRAConnector()

# 1. Catalog of monetary series, with each one's latest value
variables = connector.monetarias.list()
print(f"Found {len(variables)} series")

# 2. Latest value of a series, by ID (1 = Reservas internacionales)
latest = connector.monetarias.latest(1)
print(f"Reserves: {latest.valor} on {latest.fecha}")

# 3. Last 30 days of a series, by name (newest first, as the API returns it)
history = connector.monetarias.history("Reservas internacionales", days=30)
for point in history[:5]:
    print(point.fecha, point.valor)

# 4. Official exchange rate: pesos per dollar
usd_ars = connector.cambiarias.pair("USD", "ARS", days=7)
print(f"USD/ARS on {usd_ars[-1]['fecha']}: {usd_ars[-1]['tasa']}")
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
