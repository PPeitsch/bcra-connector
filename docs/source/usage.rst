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
   from datetime import date, datetime, timedelta
   from bcra_connector import BCRAConnector

   # Initialize the connector (default language is Spanish)
   connector = BCRAConnector()

   # For English responses, use:
   # connector = BCRAConnector(language="en-US")

Dates
-----

Every parameter that takes a date accepts a :class:`datetime.date`, a
:class:`datetime.datetime` or an ISO 8601 string, and they are interchangeable:

.. code-block:: python

   from datetime import date

   connector.cambiarias.quotations(date(2024, 6, 12))
   connector.cambiarias.quotations("2024-06-12")     # same request

A ``datetime`` has its time dropped — the BCRA API works in whole days — and a string
is parsed, so a malformed one fails immediately with a ``ValueError`` naming the
parameter instead of becoming an opaque API error:

.. code-block:: python

   connector.cambiarias.quotations("12/06/2024")
   # ValueError: 'fecha' must be an ISO 8601 date (YYYY-MM-DD), got '12/06/2024'

Dates always come **back** as :class:`datetime.date`, everywhere in the library.

Fetching Principal Variables
----------------------------

To retrieve all principal variables published by BCRA:

.. code-block:: python

   variables = connector.monetarias.list()
   for var in variables[:5]:  # Print first 5 for brevity
       print(f"{var.descripcion}: {var.ultValorInformado} ({var.ultFechaInformada})")

This returns a :class:`~bcra_connector.Page` of `PrincipalesVariables` objects, each
containing information about a specific variable including metadata like `tipoSerie`,
`periodicidad`, and `moneda`. See `Paged results`_ below.

Retrieving Historical Data
--------------------------

To fetch historical data for a specific variable:

.. code-block:: python

   id_variable = 1  # e.g., Reservas Internacionales del BCRA
   end_date = datetime.now()
   start_date = end_date - timedelta(days=30)
   response = connector.monetarias.series(id_variable, desde=start_date, hasta=end_date)
   for result in response:
       for detalle in result.detalle[:5]:  # The API returns newest first
           print(f"{detalle.fecha}: {detalle.valor}")

   print(f"{len(response)} of {response.count} available")

This returns a :class:`~bcra_connector.Page` of `DatosVariable` results, each with a
`detalle` list of `DetalleMonetaria` data points.

Getting the Latest Value
------------------------

To retrieve the most recent value for a variable:

.. code-block:: python

   latest = connector.monetarias.latest(id_variable)
   print(f"Latest value for Variable {id_variable}: {latest.valor} ({latest.fecha})")

Using the Cheques Module
------------------------

To fetch information about financial entities:

.. code-block:: python

   entities = connector.cheques.entities()
   for entity in entities[:5]:  # Print first 5 for brevity
       print(f"{entity.codigo_entidad}: {entity.denominacion}")

To check if a specific check is reported:

.. code-block:: python

   codigo_entidad = 11  # Example entity code
   numero_cheque = 20377516  # Example check number
   cheque = connector.cheques.reported(codigo_entidad, numero_cheque)
   print(f"Check {cheque.numero_cheque} is {'reported' if cheque.denunciado else 'not reported'}")

Using the Estadísticas Cambiarias Module
----------------------------------------

To fetch the list of all currencies:

.. code-block:: python

   currencies = connector.cambiarias.currencies()
   for currency in currencies[:5]:  # Print first 5 for brevity
       print(f"{currency.codigo}: {currency.denominacion}")

To get currency quotations for a specific date:

.. code-block:: python

   fecha = date(2024, 6, 12)  # a datetime or "2024-06-12" work too
   quotations = connector.cambiarias.quotations(fecha)
   for detail in quotations.detalle[:5]:  # Print first 5 for brevity
       print(f"{detail.codigo_moneda}: {detail.tipo_cotizacion}")

To fetch the evolution of a specific currency:

.. code-block:: python

   moneda = "USD"
   fecha_desde = date(2024, 6, 1)
   fecha_hasta = date(2024, 6, 30)
   evolution = connector.cambiarias.series(moneda, fecha_desde, fecha_hasta)
   for quotation in evolution[:5]:  # Print first 5 for brevity
       print(f"{quotation.fecha}: {quotation.detalle[0].tipo_cotizacion}")

Each quotation has two rates: ``tipo_cotizacion`` (pesos per unit) and ``tipo_pase``
(US dollars per unit). The API reports ``tipo_cotizacion`` as ``0`` for ARS, gold (XAU)
and silver (XAG), and ``tipo_pase`` as ``0`` for USD itself and for ``REF`` (the
Com. 3500 reference rate).

To get the evolution of a currency pair:

.. code-block:: python

   for point in connector.cambiarias.pair("USD", "ARS", days=7):
       print(f"{point['fecha']}: {point['tasa']:.2f}")  # pesos per dollar

``tasa`` follows the ``BASE/QUOTE`` convention: the amount of the quote currency for one
unit of the base currency (``EUR/USD`` ~ 1.15 dollars per euro). The rate is computed
through the dollar, so any currency with ``tipo_pase`` works (including ARS and XAU), and
a pair against USD needs a single request. ``REF`` has no dollar rate and yields no points.

Using the Central de Deudores Module
------------------------------------

The Central de Deudores endpoints live in ``connector.deudores``. To query debtor
information, historical debts, and rejected checks by CUIT/CUIL:

.. code-block:: python

   # Replace with a real CUIT/CUIL. One without records in the registry raises
   # BCRANotFoundError (see Error Handling below).
   identificacion = "20123456789"

   # Get current debts
   deudor = connector.deudores.debts(identificacion)
   print(f"Debtor: {deudor.denominacion}")
   for periodo in deudor.periodos:
       for entidad in periodo.entidades:
           print(f"- {entidad.entidad}: Situación {entidad.situacion}, ${entidad.monto}k")

   # Get historical debts (last 24 months)
   historico = connector.deudores.historical(identificacion)
   print(f"Historical periods found: {len(historico.periodos)}")

   # Get rejected checks
   rejected = connector.deudores.rejected_checks(identificacion)
   for causal in rejected.causales:
       print(f"Causal: {causal.causal}")
       for entidad in causal.entidades:
           print(f"  - Entity {entidad.entidad}: {len(entidad.detalle)} checks")

DataFrame Conversion
--------------------

Most data models include a ``to_dataframe()`` method for easy integration with data
analysis workflows. This requires ``pandas`` to be installed
(``pip install "bcra-connector[pandas]"``).

A ``Page`` converts itself, one row per result; single objects convert themselves too:

.. code-block:: python

   # Convert the catalog of principal variables to a DataFrame
   df_vars = connector.monetarias.list().to_dataframe()

   # Convert Central de Deudores info to DataFrame
   deudor = connector.deudores.debts(identificacion)
   df_deudas = deudor.to_dataframe()

   # Convert Rejected Checks to DataFrame
   rejected = connector.deudores.rejected_checks(identificacion)
   df_checks = rejected.to_dataframe()

Paged results
-------------

Every endpoint that returns more than one row answers with a
:class:`~bcra_connector.Page`. It behaves like the list it replaced — iterate it, take
its length, index it, slice it, compare it to a list — and it also carries what the API
reported about the result set:

.. code-block:: python

   page = connector.cambiarias.series("USD", limit=50)

   for quotation in page:          # iterate, as with a list
       ...
   first = page[0]                 # index
   recent = page[:10]              # slice (a plain list)

   page.count                      # total results the endpoint reported
   page.offset                     # where this page starts
   page.limit                      # page size that was asked for
   page.has_more                   # whether there is anything past this page

``count`` is the total the endpoint reported, which is not always the length of the
page: the helpers that walk the whole range (``monetarias.list()``,
``monetarias.history()``, ``cambiarias.evolution()``) already return every row, so for
them ``has_more`` is ``False``. When an endpoint reports nothing usable, ``count`` is
``None`` and ``has_more`` is ``False``.

The deprecated ``get_*`` methods still return plain lists, so existing code is
unaffected either way.

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
       deudor = connector.deudores.debts("20123456789")
   except BCRANotFoundError:
       deudor = None  # No data for this CUIT
   except BCRAServerError as e:
       print(f"BCRA unavailable (HTTP {e.status_code}), try again later")
   except BCRAApiError as e:
       print(f"Request failed: {e}")

Advanced Usage
--------------

For more advanced usage examples, including error handling, different configurations, and data visualization, please refer to the :doc:`examples` section.
