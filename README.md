# BCRA API Connector

A Python connector for the BCRA (Banco Central de la República Argentina) Estadísticas API v2.0.

## Features

- Fetch principal variables published by BCRA
- Retrieve historical data for specific variables
- Error handling with custom exceptions
- Retry logic with exponential backoff
- Type hinting for better code readability
- Logging for easier debugging

## Installation

```bash
pip install bcra-api-connector
```

## Quick Start

```python
from bcra_connector import BCRAConnector
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
```

## Documentation

For detailed documentation, use Python's built-in `help()` function or refer to the docstrings in the source code.

```python
from bcra_connector import BCRAConnector
help(BCRAConnector)
```

## Contributing

Contributions are welcome! We encourage you to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
