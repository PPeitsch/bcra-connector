Usage
=====

This guide provides an overview of how to use the BCRA API Connector for various tasks.

Initializing the Connector
--------------------------

To start using the BCRA API Connector, first import the necessary classes and create an instance of the `BCRAConnector`:

.. code-block:: python

   from bcra_connector import BCRAConnector
   from datetime import datetime, timedelta

   # Initialize the connector (default language is Spanish)
   connector = BCRAConnector()

   # For English responses, use:
   # connector = BCRAConnector(language="en-US")

Fetching Principal Variables
----------------------------

To retrieve all principal variables published by BCRA:

.. code-block:: python

   variables = connector.get_principales_variables()
   for var in variables[:5]:  # Print first 5 for brevity
       print(f"{var.descripcion}: {var.valor} ({var.fecha})")

This will return a list of `PrincipalesVariables` objects, each containing information about a specific variable.

Retrieving Historical Data
--------------------------

To fetch historical data for a specific variable:

.. code-block:: python

   id_variable = 1  # e.g., Reservas Internacionales del BCRA
   end_date = datetime.now()
   start_date = end_date - timedelta(days=30)
   datos = connector.get_datos_variable(id_variable, start_date, end_date)
   for dato in datos[-5:]:  # Print last 5 for brevity
       print(f"{dato.fecha}: {dato.valor}")

This returns a list of `DatosVariable` objects, each representing a data point for the specified variable within the given date range.

Getting the Latest Value
------------------------

To retrieve the most recent value for a variable:

.. code-block:: python

   latest = connector.get_latest_value(id_variable)
   print(f"Latest value for Variable {id_variable}: {latest.valor} ({latest.fecha})")

Using the Cheques Module
------------------------

To fetch information about financial entities:

.. code-block:: python

   entities = connector.get_entidades()
   for entity in entities[:5]:  # Print first 5 for brevity
       print(f"{entity.codigo_entidad}: {entity.denominacion}")

To check if a specific check is reported:

.. code-block:: python

   codigo_entidad = 11  # Example entity code
   numero_cheque = 20377516  # Example check number
   cheque = connector.get_cheque_denunciado(codigo_entidad, numero_cheque)
   print(f"Check {cheque.numero_cheque} is {'reported' if cheque.denunciado else 'not reported'}")

Using the Estadísticas Cambiarias Module
----------------------------------------

To fetch the list of all currencies:

.. code-block:: python

   currencies = connector.get_divisas()
   for currency in currencies[:5]:  # Print first 5 for brevity
       print(f"{currency.codigo}: {currency.denominacion}")

To get currency quotations for a specific date:

.. code-block:: python

   fecha = "2024-06-12"  # Example date
   quotations = connector.get_cotizaciones(fecha)
   for detail in quotations.detalle[:5]:  # Print first 5 for brevity
       print(f"{detail.codigo_moneda}: {detail.tipo_cotizacion}")

To fetch the evolution of a specific currency:

.. code-block:: python

   moneda = "USD"
   fecha_desde = "2024-06-01"
   fecha_hasta = "2024-06-30"
   evolution = connector.get_evolucion_moneda(moneda, fecha_desde, fecha_hasta)
   for quotation in evolution[:5]:  # Print first 5 for brevity
       print(f"{quotation.fecha}: {quotation.detalle[0].tipo_cotizacion}")

Error Handling
--------------

The connector uses custom exceptions to handle errors. Always wrap your code in try-except blocks to handle potential `BCRAApiError` exceptions:

.. code-block:: python

   from bcra_connector import BCRAApiError

   try:
       variables = connector.get_principales_variables()
   except BCRAApiError as e:
       print(f"An error occurred: {str(e)}")

Advanced Usage
--------------

For more advanced usage examples, including error handling, different configurations, and data visualization, please refer to the :doc:`examples` section.