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

Behind a proxy that inspects TLS, pass the path to its CA bundle instead of disabling
verification. A path that doesn't exist raises ``ValueError`` right away:

.. code-block:: python

   connector = BCRAConnector(verify_ssl="/etc/ssl/certs/corporate-ca.pem")

Custom Session
~~~~~~~~~~~~~~

Pass your own ``requests.Session`` to control adapters, proxies or connection pooling.
The connector sets its headers on it and uses it for every request; since the session is
yours, ``close()`` leaves it open:

.. code-block:: python

   import requests
   from requests.adapters import HTTPAdapter

   session = requests.Session()
   session.mount("https://", HTTPAdapter(pool_maxsize=50))
   session.proxies = {"https": "http://proxy.corp:8080"}

   connector = BCRAConnector(session=session)

Closing the Connection
~~~~~~~~~~~~~~~~~~~~~~

Each connector keeps a ``requests`` session with pooled connections. Call ``close()``
when you're done, or use it as a context manager:

.. code-block:: python

   from bcra_connector import BCRAConnector

   with BCRAConnector() as connector:
       latest = connector.monetarias.latest(1)

Requests are sent with ``User-Agent: bcra-connector/<version>``.

Debug Mode
~~~~~~~~~~

The connector logs through the standard ``logging`` module under the ``bcra_connector``
logger, and doesn't configure any output: nothing is printed unless your application
configures logging. To see its records, configure logging as usual:

.. code-block:: python

   import logging

   logging.basicConfig(level=logging.INFO)
   logging.getLogger("bcra_connector").setLevel(logging.DEBUG)  # only this library

``debug=True`` is a shortcut for troubleshooting: it sets the ``bcra_connector`` logger
to ``DEBUG`` and, only if no handler would receive the records, adds one that writes to
stderr.

.. code-block:: python

   from bcra_connector import BCRAConnector

   connector = BCRAConnector(debug=True)

CUIT/CUIL numbers are masked in log messages.

Retry Behavior
--------------

The connector retries transient failures (HTTP 429 and 5xx, timeouts and connection
errors) with exponential backoff: the delay is ``retry_delay * 2 ** attempt``.

- ``retries``: attempts per request before giving up (default: 3)
- ``retry_delay``: base delay between retries, in seconds (default: 1)

.. code-block:: python

   from bcra_connector import BCRAConnector

   connector = BCRAConnector(retries=5, retry_delay=2)

Catalog Cache
-------------

Name-based helpers (``monetarias.find``, ``monetarias.history``) and
``cheques.is_reported`` look names up in reference catalogs: the variables catalog and
the list of financial entities. Each connector instance reuses those catalogs for
``cache_ttl`` seconds (default: 300) instead of downloading them on every lookup.

- ``connector.clear_cache()`` drops the cached catalogs so the next lookup refetches them.
- ``cache_ttl=0`` disables the cache.
- ``monetarias.list()`` and ``cheques.entities()`` are never cached: call them
  when you need fresh data (the catalog includes each series' latest value).

.. code-block:: python

   connector = BCRAConnector(cache_ttl=0)

Transport
---------

The remaining transport knobs, all constructor arguments with sensible defaults:

- ``base_url``: root of the BCRA API (default: ``"https://api.bcra.gob.ar"``). Point it
  at a mock server or a proxy when testing.
- ``page_size``: page size asked of Monetarias v4.0 (default: 3000, the largest it
  accepts; without an explicit limit the API returns 1000).
- ``fx_page_size``: page size asked of Estadísticas Cambiarias v1.0 (default: 1000, the
  largest it accepts).
- ``max_pages``: safety cap on how many pages the helpers that walk a whole range will
  fetch (default: 100). It stops a paging loop against an endpoint that ignores
  ``Offset``.

.. code-block:: python

   connector = BCRAConnector(base_url="http://localhost:8080", page_size=100)

Every setting is fixed when the connector is constructed: build another instance to
configure it differently.
