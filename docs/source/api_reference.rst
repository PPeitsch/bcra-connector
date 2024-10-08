API Reference
=============

This section provides a detailed reference for the BCRA API Connector's classes and methods.

BCRAConnector
-------------

.. py:class:: BCRAConnector(language="es-AR", verify_ssl=True, debug=False)

   The main class for interacting with the BCRA API.

   :param language: Language for API responses. Options: "es-AR" (default), "en-US".
   :type language: str
   :param verify_ssl: Whether to verify SSL certificates. Default is True.
   :type verify_ssl: bool
   :param debug: Enable debug logging. Default is False.
   :type debug: bool

Methods
^^^^^^^

.. py:method:: get_principales_variables()

   Fetch all principal variables published by BCRA.

   :return: A list of principal variables.
   :rtype: List[PrincipalesVariables]
   :raises BCRAApiError: If the API request fails.

.. py:method:: get_datos_variable(id_variable: int, desde: datetime, hasta: datetime)

   Fetch historical data for a specific variable within a date range.

   :param id_variable: The ID of the desired variable.
   :type id_variable: int
   :param desde: The start date of the range to query.
   :type desde: datetime
   :param hasta: The end date of the range to query.
   :type hasta: datetime
   :return: A list of historical data points.
   :rtype: List[DatosVariable]
   :raises BCRAApiError: If the API request fails.
   :raises ValueError: If the date range is invalid.

.. py:method:: get_latest_value(id_variable: int)

   Fetch the latest value for a specific variable.

   :param id_variable: The ID of the desired variable.
   :type id_variable: int
   :return: The latest data point for the specified variable.
   :rtype: DatosVariable
   :raises BCRAApiError: If the API request fails or if no data is available.

Data Classes
------------

PrincipalesVariables
^^^^^^^^^^^^^^^^^^^^

.. py:class:: PrincipalesVariables

   Represents a principal variable from the BCRA API.

   :param id_variable: The ID of the variable.
   :type id_variable: int
   :param cd_serie: The series code of the variable.
   :type cd_serie: int
   :param descripcion: The description of the variable.
   :type descripcion: str
   :param fecha: The date of the variable's value.
   :type fecha: str
   :param valor: The value of the variable.
   :type valor: float

DatosVariable
^^^^^^^^^^^^^

.. py:class:: DatosVariable

   Represents historical data for a variable.

   :param id_variable: The ID of the variable.
   :type id_variable: int
   :param fecha: The date of the data point.
   :type fecha: str
   :param valor: The value of the variable on the given date.
   :type valor: float

Exceptions
----------

.. py:exception:: BCRAApiError

   Custom exception for BCRA API errors.

   This exception is raised when an API request fails, either due to network issues, authentication problems, or invalid data.

Constants
---------

.. py:data:: BASE_URL

   The base URL for the BCRA API.

.. py:data:: MAX_RETRIES

   Maximum number of retry attempts for failed requests. Default is 3.

.. py:data:: RETRY_DELAY

   Initial delay (in seconds) between retry attempts. Default is 1.

This API reference provides a comprehensive overview of the BCRA API Connector's functionality. For usage examples and best practices, refer to the :doc:`usage` and :doc:`examples` sections.