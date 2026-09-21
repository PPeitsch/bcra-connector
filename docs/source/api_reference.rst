API Reference
=============

This section provides a detailed reference for the BCRA API Connector's classes and
methods, automatically generated from the source code.

BCRAConnector
-------------

The facade: configuration, lifecycle and the four domain clients below. Its own
``get_*`` methods are deprecated aliases kept until 1.0; new code calls the clients.

.. automodule:: src.bcra_connector.bcra_connector
   :members:
   :undoc-members:
   :show-inheritance:

Domain Clients
--------------

One per BCRA API, reached as ``connector.monetarias``, ``connector.cheques``,
``connector.cambiarias`` and ``connector.deudores``.

.. automodule:: src.bcra_connector.clients.monetarias
   :members:
   :show-inheritance:

.. automodule:: src.bcra_connector.clients.cheques
   :members:
   :show-inheritance:

.. automodule:: src.bcra_connector.clients.cambiarias
   :members:
   :show-inheritance:

.. automodule:: src.bcra_connector.clients.deudores
   :members:
   :show-inheritance:

Shared Models
-------------

.. automodule:: src.bcra_connector.models
   :members:
   :undoc-members:
   :show-inheritance:

Exceptions
----------

.. automodule:: src.bcra_connector.exceptions
   :members:
   :show-inheritance:

Principales Variables (Monetarias v4.0)
---------------------------------------

.. automodule:: src.bcra_connector.principales_variables.principales_variables
   :members:
   :undoc-members:
   :show-inheritance:

Cheques
-------

.. automodule:: src.bcra_connector.cheques.cheques
   :members:
   :undoc-members:
   :show-inheritance:

Estadísticas Cambiarias
-----------------------

.. automodule:: src.bcra_connector.estadisticas_cambiarias.estadisticas_cambiarias
   :members:
   :undoc-members:
   :show-inheritance:

Rate Limiter
------------

.. automodule:: src.bcra_connector.rate_limiter
   :members:
   :undoc-members:
   :show-inheritance:

Timeout Config
--------------

.. automodule:: src.bcra_connector.timeout_config
   :members:
   :undoc-members:
   :show-inheritance:
