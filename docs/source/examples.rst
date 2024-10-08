Examples
========

This section provides detailed examples of how to use the BCRA API Connector for various tasks.

Fetching Principal Variables
----------------------------

The following example demonstrates how to fetch and visualize the principal variables from the BCRA API.

.. literalinclude:: ../../examples/01_get_principales_variables.py
   :language: python
   :lines: 11-

This script will generate a bar plot of the top 10 principal variables:

.. image:: /_static/images/principal_variables.png
   :alt: Top 10 Principal Variables

Retrieving Historical Data
--------------------------

This example shows how to retrieve historical data for a specific variable and plot it.

.. literalinclude:: ../../examples/02_get_datos_variable.py
   :language: python
   :lines: 11-

The script generates a line plot of the variable's values over time:

.. image:: /_static/images/variable_1_data.png
   :alt: Historical Data for Variable 1

Getting Latest Values
---------------------

Here's how to fetch and compare the latest values for multiple variables.

.. literalinclude:: ../../examples/03_get_latest_value.py
   :language: python
   :lines: 11-

This example creates a bar plot comparing the latest values:

.. image:: /_static/images/latest_values.png
   :alt: Latest Values Comparison

Error Handling
--------------

The following example demonstrates how the connector handles various error scenarios.

.. literalinclude:: ../../examples/04_error_handling.py
   :language: python
   :lines: 11-

Connector Configuration
-----------------------

This example showcases different configuration options for the BCRA API Connector.

.. literalinclude:: ../../examples/05_connector_configuration.py
   :language: python
   :lines: 11-

These examples provide a comprehensive overview of the BCRA API Connector's capabilities and usage patterns.

