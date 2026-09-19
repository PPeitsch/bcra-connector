Welcome to BCRA API Connector's documentation!
==============================================

The BCRA API Connector is a Python library that provides a convenient interface to interact with the public APIs of the BCRA (Banco Central de la República Argentina):

* Estadísticas Monetarias v4.0 (principal variables and monetary series)
* Cheques Denunciados v1.0
* Estadísticas Cambiarias v1.0
* Central de Deudores v1.0

Features
--------

* Fetch the catalog of monetary series and their full history (paginated automatically)
* Get the latest value for a variable, or look it up by name
* Check whether a cheque is reported, by entity name
* Retrieve exchange rates, currency evolution and currency pairs
* Query debts and rejected cheques by CUIT/CUIL
* Typed dataclasses for every response, with optional pandas conversion
* Typed exceptions (``BCRANotFoundError``, ``BCRARateLimitError``, ``BCRAServerError``)
* Retries with exponential backoff, rate limiting and configurable timeouts
* Library-friendly logging: silent unless your application configures it

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   examples
   configuration
   api_reference
   changelog
   contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
