# Configuring the BCRA API Connector

The BCRA API Connector offers various configuration options to tailor its behavior to your specific needs. This guide explains each option in detail and provides examples of when and how to use them.

## Initialization Options

When creating a new instance of `BCRAConnector`, you can customize its behavior using the following parameters:

```python
from bcra_connector import BCRAConnector

connector = BCRAConnector(
    language="es-AR",
    verify_ssl=True,
    debug=False
)
```

### Language Setting

The `language` parameter determines the language for API responses.

- **Options**: 
  - `"es-AR"` (default): Spanish (Argentina)
  - `"en-US"`: English (United States)

**Example:**
```python
connector = BCRAConnector(language="en-US")
```

**Use case:** Set to "en-US" if you prefer English responses or are building an English-language application.

### SSL Verification

The `verify_ssl` parameter controls whether SSL certificates are verified during API requests.

- **Options**:
  - `True` (default): Verify SSL certificates
  - `False`: Disable SSL verification

**Example:**
```python
connector = BCRAConnector(verify_ssl=False)
```

**Warning:** Disabling SSL verification is not recommended for production use as it may expose you to security risks.

**Use case:** Temporarily disable during development if encountering SSL-related issues, or when working in environments with self-signed certificates.

### Debug Mode

The `debug` parameter enables detailed logging for troubleshooting.

- **Options**:
  - `False` (default): Normal logging
  - `True`: Verbose debug logging

**Example:**
```python
connector = BCRAConnector(debug=True)
```

**Use case:** Enable when you need to diagnose issues or want to understand the connector's internal operations.

## Advanced Configuration

For more advanced use cases, you can modify the connector's retry behavior by subclassing `BCRAConnector`:

```python
class CustomBCRAConnector(BCRAConnector):
    MAX_RETRIES = 5
    RETRY_DELAY = 2

connector = CustomBCRAConnector()
```

### Retry Mechanism

- `MAX_RETRIES`: Maximum number of retry attempts (default: 3)
- `RETRY_DELAY`: Initial delay between retries in seconds (default: 1)

**Use case:** Increase `MAX_RETRIES` and `RETRY_DELAY` when working with unstable network connections or during high-traffic periods.

## Best Practices

1. **Production Settings:** Always use SSL verification in production environments.
2. **Localization:** Choose the appropriate language setting based on your target audience.
3. **Debugging:** Use debug mode sparingly, as it can generate large log files.
4. **Retry Tuning:** Adjust retry settings based on your specific use case and the API's behavior.

By leveraging these configuration options, you can optimize the BCRA API Connector's performance and reliability for your specific use case.
