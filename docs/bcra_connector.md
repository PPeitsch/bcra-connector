# BCRA API Connector Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Usage](#usage)
4. [API Reference](#api-reference)
5. [Error Handling](#error-handling)
6. [Examples](#examples)

## Introduction

The BCRA API Connector is a Python library that provides a convenient interface to interact with the BCRA (Banco Central de la República Argentina) Estadísticas API v2.0. It allows users to fetch principal variables and historical data from the BCRA.

## Installation

To install the BCRA API Connector, run the following command:

```bash
pip install bcra-api-connector
```

## Usage

Here's a basic example of how to use the BCRA API Connector:

```python
from bcra_connector import BCRAConnector
from datetime import datetime, timedelta

connector = BCRAConnector()

# Get principal variables
variables = connector.get_principales_variables()

# Get historical data for a specific variable
id_variable = 1
end_date = datetime.now()
start_date = end_date - timedelta(days=30)
datos = connector.get_datos_variable(id_variable, start_date, end_date)

# Get the latest value for a variable
latest = connector.get_latest_value(id_variable)
```

## API Reference

### `BCRAConnector`

The main class for interacting with the BCRA API.

#### Methods

- `get_principales_variables() -> List[PrincipalesVariables]`
  
  Fetches the list of all variables published by BCRA.

- `get_datos_variable(id_variable: int, desde: datetime, hasta: datetime) -> List[DatosVariable]`
  
  Fetches the list of values for a variable within a specified date range.

- `get_latest_value(id_variable: int) -> DatosVariable`
  
  Fetches the latest value for a specific variable.

### Data Classes

#### `PrincipalesVariables`

Represents a principal variable from the BCRA API.

Attributes:
- `id_variable: int`
- `cd_serie: int`
- `descripcion: str`
- `fecha: str`
- `valor: float`

#### `DatosVariable`

Represents historical data for a variable.

Attributes:
- `id_variable: int`
- `fecha: str`
- `valor: float`

## Error Handling

The connector uses a custom `BCRAApiError` exception for API-related errors. It's recommended to catch this exception when using the connector:

```python
from bcra_connector import BCRAConnector, BCRAApiError

connector = BCRAConnector()

try:
    variables = connector.get_principales_variables()
except BCRAApiError as e:
    print(f"An error occurred: {str(e)}")
```

## Examples

For more examples, please refer to the [examples](examples/) directory in the repository.
