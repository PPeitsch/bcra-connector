Examples
========

This section provides detailed examples of how to use the BCRA API Connector for various tasks.

Fetching Principal Variables
----------------------------

The following example demonstrates how to fetch and visualize the principal variables from the BCRA API.

.. literalinclude:: ../../examples/01_get_principales_variables.py
   :language: python
   :lines: 6-

Running it saves a bar plot of the top 10 principal variables to
``docs/build/_static/images/``.

Retrieving Historical Data
--------------------------

This example shows how to retrieve historical data for a specific variable and plot it.

.. literalinclude:: ../../examples/02_get_datos_variable.py
   :language: python
   :lines: 6-

Running it saves a line plot of the variable's values over time.

Getting Latest Values
---------------------

Here's how to fetch and compare the latest values for multiple variables.

.. literalinclude:: ../../examples/03_get_latest_value.py
   :language: python
   :lines: 6-

Running it saves a bar plot comparing the latest values.

Error Handling
--------------

The following example demonstrates how the connector handles various error scenarios.

.. literalinclude:: ../../examples/04_error_handling.py
   :language: python
   :lines: 6-

Connector Configuration
-----------------------

This example showcases different configuration options for the BCRA API Connector.

.. literalinclude:: ../../examples/05_connector_configuration.py
   :language: python
   :lines: 6-

Cheques Module Usage
--------------------

This example demonstrates how to interact with the Cheques API, including fetching financial entities and checking for reported checks.

.. literalinclude:: ../../examples/06_cheques_api.py
   :language: python
   :lines: 6-

Exchange Statistics Usage
-------------------------

This example shows how to use the Exchange Statistics (Estadísticas Cambiarias) API to fetch currencies, quotations, and evolution data.

.. literalinclude:: ../../examples/07_exchange_statistics.py
   :language: python
   :lines: 6-

These examples provide a comprehensive overview of the BCRA API Connector's capabilities and usage patterns.
