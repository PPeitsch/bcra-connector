Configuration
=============

The BCRA API Connector offers several configuration options to customize its behavior. This guide explains each option and how to use it.

Initialization Options
----------------------

When creating a new instance of the `BCRAConnector`, you can pass the following parameters:

.. code-block:: python

   from bcra_connector import BCRAConnector

   connector = BCRAConnector(
       language="es-AR",
       verify_ssl=True,
       debug=False
   )

Language
~~~~~~~~

The `language` parameter sets the language for API responses. Available options are:

- `"es-AR"` (default): Spanish (Argentina)
- `"en-US"`: English (United States)

Example:

.. code-block:: python

   from bcra_connector import BCRAConnector

   connector = BCRAConnector(language="en-US")

SSL Verification
~~~~~~~~~~~~~~~~

The `verify_ssl` parameter determines whether SSL certificates should be verified during API requests. By default, it's set to `True`.

To disable SSL verification (not recommended for production):

.. code-block:: python

   from bcra_connector import BCRAConnector

   connector = BCRAConnector(verify_ssl=False)

Debug Mode
~~~~~~~~~~

The `debug` parameter enables detailed logging when set to `True`. This is useful for troubleshooting.

Example:

.. code-block:: python

   from bcra_connector import BCRAConnector

   connector = BCRAConnector(debug=True)

Retry Behavior
--------------

The connector implements a retry mechanism with exponential backoff. You can modify this behavior by changing the following class variables:

- `MAX_RETRIES`: Maximum number of retry attempts (default: 3)
- `RETRY_DELAY`: Initial delay between retries in seconds (default: 1)

To change these values, subclass `BCRAConnector`:

.. code-block:: python

   from bcra_connector import BCRAConnector

   class CustomBCRAConnector(BCRAConnector):
       MAX_RETRIES = 5
       RETRY_DELAY = 2

   connector = CustomBCRAConnector()

Catalog Cache
-------------

Name-based helpers (``get_variable_by_name``, ``get_variable_history``,
``generate_variable_report``, ``get_variable_correlation``) and ``check_denunciado`` look
names up in reference catalogs: the variables catalog and the list of financial
entities. Each connector instance reuses those catalogs for ``CATALOG_CACHE_TTL`` seconds
(default: 300) instead of downloading them on every lookup.

- ``connector.clear_cache()`` drops the cached catalogs so the next lookup refetches them.
- ``CATALOG_CACHE_TTL = 0`` disables the cache.
- ``get_principales_variables()`` and ``get_entidades()`` are never cached: call them
  when you need fresh data (the catalog includes each series' latest value).

.. code-block:: python

   class NoCacheConnector(BCRAConnector):
       CATALOG_CACHE_TTL = 0

This configuration provides more flexibility and control over the connector's behavior.
