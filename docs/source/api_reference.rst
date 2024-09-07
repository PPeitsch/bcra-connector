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

**Note:** Disabling SSL verification (`verify_ssl=False`) is not recommended in production environments as it may expose your application to security risks. Only use this option in development environments or when dealing with self-signed certificates.

### Methods

```{py:method} get_principales_variables()
```

Fetch all principal variables published by BCRA.

**Returns:**
List[PrincipalesVariables]: A list of principal variables.

**Raises:**
BCRAApiError: If the API request fails.

**Example response:**
```python
[
    PrincipalesVariables(
        id_variable=1,
        cd_serie=246,
        descripcion="Reservas Internacionales del BCRA",
        fecha="2024-09-07",
        valor=27755.0
    ),
    # ... more variables
]
```

---

```{py:method} get_datos_variable(id_variable: int, desde: datetime, hasta: datetime)
```

Fetch historical data for a specific variable within a date range.

**Parameters:**
- `id_variable` (int): The ID of the desired variable.
- `desde` (datetime): The start date of the range to query (inclusive).
- `hasta` (datetime): The end date of the range to query (inclusive).

**Returns:**
List[DatosVariable]: A list of historical data points.

**Raises:**
- BCRAApiError: If the API request fails.
- ValueError: If the date range is invalid.

**Note:** Dates should be provided as Python `datetime` objects. The API uses the date format "YYYY-MM-DD" internally.

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

**Note:** The BCRA typically updates data daily, but update frequency may vary by variable. Check the `fecha` field in the response for the exact date of the latest value.

## Data Classes

### PrincipalesVariables

```{py:class} PrincipalesVariables
```

Represents a principal variable from the BCRA API.

**Attributes:**
- `id_variable` (int): The ID of the variable.
- `cd_serie` (int): The series code of the variable.
- `descripcion` (str): The description of the variable.
- `fecha` (str): The date of the variable's value (format: "YYYY-MM-DD").
- `valor` (float): The value of the variable.

### DatosVariable

```{py:class} DatosVariable
```

Represents historical data for a variable.

**Attributes:**
- `id_variable` (int): The ID of the variable.
- `fecha` (str): The date of the data point (format: "YYYY-MM-DD", timezone: ART - Argentina Time).
- `valor` (float): The value of the variable on the given date.

## Exceptions

### BCRAApiError

```{py:exception} BCRAApiError
```

Custom exception for BCRA API errors.

This exception is raised when an API request fails, either due to network issues, authentication problems, or invalid data.

Common error scenarios:
- 400 Bad Request: Invalid parameters or date range
- 404 Not Found: Requested resource not available
- 500 Internal Server Error: BCRA API server issues

## Constants

- `BASE_URL`: The base URL for the BCRA API.
- `MAX_RETRIES` (default: 3): Maximum number of retry attempts for failed requests.
- `RETRY_DELAY` (default: 1): Initial delay (in seconds) between retry attempts.

This API reference provides a comprehensive overview of the BCRA API Connector's functionality. For usage examples and best practices, refer to the [Usage Guide](usage.rst) and [Examples](examples.rst) sections.
