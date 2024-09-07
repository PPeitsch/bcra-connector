# Using the BCRA API Connector

This guide will walk you through the main features of the BCRA API Connector, demonstrating how to retrieve and work with economic data from the Banco Central de la República Argentina.

## Getting Started

First, import the necessary classes and create an instance of the `BCRAConnector`:

```python
from bcra_connector import BCRAConnector
from datetime import datetime, timedelta

# Initialize the connector (default language is Spanish)
connector = BCRAConnector()

# For English responses, use:
# connector = BCRAConnector(language="en-US")
```

## Fetching Principal Variables

To get an overview of the main economic indicators:

```python
variables = connector.get_principales_variables()

for var in variables[:5]:  # Display first 5 for brevity
    print(f"{var.descripcion}: {var.valor} ({var.fecha})")
```

This will return a list of `PrincipalesVariables` objects, each representing a key economic indicator.

## Retrieving Historical Data

To analyze trends, you can fetch historical data for a specific variable:

```python
# Example: Fetch data for Reservas Internacionales del BCRA (usually ID 1)
id_variable = 1
end_date = datetime.now()
start_date = end_date - timedelta(days=30)  # Last 30 days

datos = connector.get_datos_variable(id_variable, start_date, end_date)

for dato in datos[-5:]:  # Display last 5 data points
    print(f"{dato.fecha}: {dato.valor}")
```

This returns a list of `DatosVariable` objects, each representing a data point within the specified date range.

## Getting the Latest Value

For the most up-to-date information on a specific indicator:

```python
latest = connector.get_latest_value(id_variable)
print(f"Latest value for Variable {id_variable}: {latest.valor} ({latest.fecha})")
```

## Error Handling

The connector uses custom exceptions for error handling. Always wrap your code in try-except blocks:

```python
from bcra_connector import BCRAApiError

try:
    variables = connector.get_principales_variables()
except BCRAApiError as e:
    print(f"An error occurred: {str(e)}")
```

## Advanced Usage Tips

1. **Date Ranges**: When fetching historical data, ensure your date range doesn't exceed one year.
2. **SSL Verification**: If you encounter SSL issues, you can disable verification (use with caution):
   ```python
   connector = BCRAConnector(verify_ssl=False)
   ```
3. **Debugging**: Enable debug mode for detailed logging:
   ```python
   connector = BCRAConnector(debug=True)
   ```

For more advanced usage examples, including data visualization and analysis, check out our [Examples](examples.rst) section.
