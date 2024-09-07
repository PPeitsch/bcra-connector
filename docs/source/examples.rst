# BCRA API Connector Examples

This section provides in-depth examples of how to use the BCRA API Connector for various tasks, from basic data retrieval to more complex scenarios involving data analysis and visualization.

## 1. Fetching and Visualizing Principal Variables

This example demonstrates how to fetch the principal variables and create a bar plot of the top 10.

```python
{literalinclude} ../../examples/01_get_principales_variables.py
:language: python
:lines: 11-
```

This script will generate a bar plot of the top 10 principal variables:

![Top 10 Principal Variables](/_static/images/principal_variables.png)

**Key Takeaways:**
- Use `get_principales_variables()` to fetch all main indicators.
- Handle potential SSL issues by retrying without SSL verification.
- Utilize matplotlib for creating informative visualizations.

## 2. Retrieving and Plotting Historical Data

This example shows how to fetch historical data for a specific variable (e.g., International Reserves) and plot it over time.

```python
{literalinclude} ../../examples/02_get_datos_variable.py
:language: python
:lines: 11-
```

The script generates a line plot of the variable's values over time:

![Historical Data for Variable 1](/_static/images/variable_1_data.png)

**Key Takeaways:**
- Use `get_datos_variable()` with specific date ranges.
- Convert string dates to datetime objects for proper plotting.
- Visualize trends over time using line plots.

## 3. Comparing Latest Values for Multiple Variables

This example demonstrates how to fetch and compare the latest values for multiple variables.

```python
{literalinclude} ../../examples/03_get_latest_value.py
:language: python
:lines: 11-
```

This script creates a bar plot comparing the latest values:

![Latest Values Comparison](/_static/images/latest_values.png)

**Key Takeaways:**
- Use `get_latest_value()` for quick access to current data.
- Compare multiple indicators side by side using bar plots.
- Handle potential errors for each variable independently.

## 4. Error Handling Scenarios

This example showcases how the connector handles various error scenarios.

```python
{literalinclude} ../../examples/04_error_handling.py
:language: python
:lines: 11-
```

**Key Takeaways:**
- Test different error scenarios (invalid IDs, date ranges, etc.).
- Use try-except blocks to catch and handle `BCRAApiError`.
- Log errors and unexpected successes for debugging.

## 5. Exploring Connector Configurations

This example demonstrates different configuration options for the BCRA API Connector.

```python
{literalinclude} ../../examples/05_connector_configuration.py
:language: python
:lines: 11-
```

**Key Takeaways:**
- Experiment with different connector configurations (SSL, debug mode, language).
- Compare behavior and performance across different settings.
- Use debug mode for detailed logging when troubleshooting.

These examples provide a comprehensive overview of the BCRA API Connector's capabilities and usage patterns. By studying and adapting these examples, you'll be well-equipped to integrate BCRA data into your own projects and analyses.
