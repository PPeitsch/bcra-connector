# API Reference

This section provides a detailed reference for the BCRA API Connector's classes and methods.

## BCRAConnector

```{py:class} BCRAConnector(language="es-AR", verify_ssl=True, debug=False)
```

The main class for interacting with the BCRA API.

### Parameters

- `language` (str, optional): Language for API responses. Options: "es-AR" (default), "en-US".
- `verify_ssl` (bool, optional): Whether to verify SSL certificates. Default is True.
- `debug` (bool, optional): Enable debug logging. Default is False.

### Methods

```{py:method} get_principales_variables()
```

Fetch all principal variables published by BCRA.

**Returns:**
List[PrincipalesVariables]: A list of principal variables.

**Raises:**
BCRAApiError: If the API request fails.

---

```{py:method} get_datos_variable(id_variable: int, desde: datetime, hasta: datetime)
```

Fetch historical data for a specific variable within a date range.

**Parameters:**
- `id_variable` (int): The ID of the desired variable.
- `desde` (datetime): The start date of the range to query.
- `hasta` (datetime): The end date of the range to query.

**Returns:**
List[DatosVariable]: A list of historical data points.

**Raises:**
- BCRAApiError: If the API request fails.
- ValueError: If the date range is invalid.

---

```{py:method} get_latest_value(id_variable: int)
```

Fetch the latest value for a specific variable.

**Parameters:**
- `id_variable` (int): The ID of the desired variable.

**Returns:**
DatosVariable: The latest data point for the specified variable.

**Raises:**
BCRAApiError: If the API request fails or if no data is available.

## Data Classes

### PrincipalesVariables

```{py:class} PrincipalesVariables
```

Represents a principal variable from the BCRA API.

**Attributes:**
- `id_variable` (int): The ID of the variable.
- `cd_serie` (int): The series code of the variable.
- `descripcion` (str): The description of the variable.
- `fecha` (str): The date of the variable's value.
- `valor` (float): The value of the variable.

### DatosVariable

```{py:class} DatosVariable
```

Represents historical data for a variable.

**Attributes:**
- `id_variable` (int): The ID of the variable.
- `fecha` (str): The date of the data point.
- `valor` (float): The value of the variable on the given date.

## Exceptions

### BCRAApiError

```{py:exception} BCRAApiError
```

Custom exception for BCRA API errors.

This exception is raised when an API request fails, either due to network issues, authentication problems, or invalid data.

## Constants

- `BASE_URL`: The base URL for the BCRA API.
- `MAX_RETRIES`: Maximum number of retry attempts for failed requests.
- `RETRY_DELAY`: Initial delay (in seconds) between retry attempts.

This API reference provides a comprehensive overview of the BCRA API Connector's functionality. For usage examples and best practices, refer to the [Usage Guide](usage.rst) and [Examples](examples.rst) sections.
