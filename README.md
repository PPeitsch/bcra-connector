# BCRA API Connector

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

## Installation

```bash
pip install bcra-connector
```

## Requirements

- Python 3.9 or higher
- requests>=2.32.0,<2.33
- matplotlib>=3.7.3,<3.8
- setuptools>=70.0.0,<71
- urllib3>=2.2.1,<3.0
- numpy~=1.26.4,<1.27
- scipy~=1.14.1,<1.15

## Quick Start

```python
from src.bcra_connector import BCRAConnector
from datetime import datetime, timedelta

# Initialize the connector
connector = BCRAConnector()

# Get all principal variables
variables = connector.get_principales_variables()
for var in variables[:5]:  # Print first 5 for brevity
    print(f"{var.descripcion}: {var.valor} ({var.fecha})")

# Get data for a specific variable (e.g., Reservas Internacionales del BCRA)
id_variable = 1
end_date = datetime.now()
start_date = end_date - timedelta(days=30)
datos = connector.get_datos_variable(id_variable, start_date, end_date)
for dato in datos[-5:]:  # Print last 5 for brevity
    print(f"{dato.fecha}: {dato.valor}")

# Get the latest value for a variable
latest = connector.get_latest_value(id_variable)
print(f"Latest value for Variable {id_variable}: {latest.valor} ({latest.fecha})")

# Get information about reported checks
entities = connector.get_entidades()
cheque = connector.get_cheque_denunciado(entities[0].codigo_entidad, 12345678)
print(f"Check status: {'Reported' if cheque.denunciado else 'Not reported'}")

# Get currency exchange rates
currencies = connector.get_divisas()
quotations = connector.get_cotizaciones()
for detail in quotations.detalle[:5]:  # Print first 5 for brevity
    print(f"{detail.codigo_moneda}: {detail.tipo_cotizacion}")
```

## Documentation

For detailed documentation, including usage examples and API reference, please visit our [Read The Docs Documentation](https://bcra-connector.readthedocs.io/).

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and suggest improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

For a detailed list of changes and version updates, please refer to the [Changelog](https://bcra-connector.readthedocs.io/en/latest/changelog.html).

## Disclaimer

This project is not officially affiliated with or endorsed by the Banco Central de la República Argentina. Use at your own risk.