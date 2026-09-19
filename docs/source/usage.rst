Usage
=====

This guide provides an overview of how to use the BCRA API Connector for various tasks.

Initializing the Connector
--------------------------

To start using the BCRA API Connector, first import the necessary classes and create an instance of the `BCRAConnector`:

.. code-block:: python

   import os
   import sys
   import logging
   from datetime import datetime, timedelta
   from bcra_connector import BCRAConnector

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
       print(f"{var.descripcion}: {var.ultValorInformado} ({var.ultFechaInformada})")

This will return a list of `PrincipalesVariables` objects, each containing information about a specific variable including metadata like `tipoSerie`, `periodicidad`, and `moneda`.

Retrieving Historical Data
--------------------------

To fetch historical data for a specific variable:

.. code-block:: python

   id_variable = 1  # e.g., Reservas Internacionales del BCRA
   end_date = datetime.now()
   start_date = end_date - timedelta(days=30)
   response = connector.get_datos_variable(id_variable, desde=start_date, hasta=end_date)
   for result in response.results:
       for detalle in result.detalle[-5:]:  # Print last 5 for brevity
           print(f"{detalle.fecha}: {detalle.valor}")

This returns a `DatosVariableResponse` object containing metadata and a list of `DatosVariable` results, each with a `detalle` list of `DetalleMonetaria` data points.

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

Each quotation has two rates: ``tipo_cotizacion`` (pesos per unit) and ``tipo_pase``
(US dollars per unit). The API reports ``tipo_cotizacion`` as ``0`` for ARS, gold (XAU)
and silver (XAG), and ``tipo_pase`` as ``0`` for USD itself and for ``REF`` (the
Com. 3500 reference rate).

To get the evolution of a currency pair:

.. code-block:: python

   for point in connector.get_currency_pair_evolution("USD", "ARS", days=7):
       print(f"{point['fecha']}: {point['tasa']:.2f}")  # pesos per dollar

``tasa`` follows the ``BASE/QUOTE`` convention: the amount of the quote currency for one
unit of the base currency (``EUR/USD`` ~ 1.15 dollars per euro). The rate is computed
through the dollar, so any currency with ``tipo_pase`` works (including ARS and XAU), and
a pair against USD needs a single request. ``REF`` has no dollar rate and yields no points.

Using the Central de Deudores Module
------------------------------------

To query debtor information, historical debts, and rejected checks by CUIT/CUIL:

.. code-block:: python

   identificacion = "20123456789"  # Example CUIT

   # Get current debts
   deudor = connector.get_deudas(identificacion)
   print(f"Debtor: {deudor.denominacion}")
   for periodo in deudor.periodos:
       for entidad in periodo.entidades:
           print(f"- {entidad.entidad}: Situación {entidad.situacion}, ${entidad.monto}k")

   # Get historical debts (last 24 months)
   historico = connector.get_deudas_historicas(identificacion)
   print(f"Historical periods found: {len(historico.periodos)}")

   # Get rejected checks
   rejected = connector.get_cheques_rechazados(identificacion)
   for causal in rejected.causales:
       print(f"Causal: {causal.causal}")
       for entidad in causal.entidades:
           print(f"  - Entity {entidad.entidad}: {len(entidad.detalle)} checks")

DataFrame Conversion
--------------------

Most data models include a `to_dataframe()` method for easy integration with data analysis workflows. This requires `pandas` to be installed (``pip install bcra-connector[pandas]``).

.. code-block:: python

   # Convert Principal Variables to DataFrame
   variables = connector.get_principales_variables()
   df_vars = variables.to_dataframe()

   # Convert Central de Deudores info to DataFrame
   deudor = connector.get_deudas(identificacion)
   df_deudas = deudor.to_dataframe()

   # Convert Rejected Checks to DataFrame
   rejected = connector.get_cheques_rechazados(identificacion)
   df_checks = rejected.to_dataframe()

Error Handling
--------------

Every API failure raises ``BCRAApiError`` or one of its subclasses, so catching
``BCRAApiError`` handles all of them. The subclasses and the ``status_code`` attribute
(``None`` when there was no HTTP response, e.g. a timeout) let you react to specific
outcomes without parsing messages:

- ``BCRANotFoundError``: HTTP 404 (unknown variable, CUIT without data, unknown entity).
- ``BCRARateLimitError``: HTTP 429 that persisted after the retries.
- ``BCRAServerError``: HTTP 5xx that persisted after the retries.

Invalid arguments raise ``ValueError`` instead: a negative ``days``, a CUIT that isn't
11 digits, or an entity name in ``check_denunciado()`` that matches no entity or
several.

.. code-block:: python

   from bcra_connector import (
       BCRAApiError,
       BCRAConnector,
       BCRANotFoundError,
       BCRAServerError,
   )

   connector = BCRAConnector()
   try:
       deudor = connector.get_deudas("20123456789")
   except BCRANotFoundError:
       deudor = None  # No data for this CUIT
   except BCRAServerError as e:
       print(f"BCRA unavailable (HTTP {e.status_code}), try again later")
   except BCRAApiError as e:
       print(f"Request failed: {e}")

Advanced Usage
--------------

For more advanced usage examples, including error handling, different configurations, and data visualization, please refer to the :doc:`examples` section.
