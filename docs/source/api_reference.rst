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

.. py:method:: get_entidades()

   Fetch the list of all financial entities.

   :return: A list of financial entities.
   :rtype: List[Entidad]
   :raises BCRAApiError: If the API request fails.

.. py:method:: get_cheque_denunciado(codigo_entidad: int, numero_cheque: int)

   Fetch information about a reported check.

   :param codigo_entidad: The code of the financial entity.
   :type codigo_entidad: int
   :param numero_cheque: The check number.
   :type numero_cheque: int
   :return: Information about the reported check.
   :rtype: Cheque
   :raises BCRAApiError: If the API request fails or returns unexpected data.

.. py:method:: get_divisas()

   Fetch the list of all currencies.

   :return: A list of currencies.
   :rtype: List[Divisa]
   :raises BCRAApiError: If the API request fails or returns unexpected data.

.. py:method:: get_cotizaciones(fecha: Optional[str] = None)

   Fetch currency quotations for a specific date.

   :param fecha: The date for which to fetch quotations (format: YYYY-MM-DD), defaults to None (latest date).
   :type fecha: Optional[str]
   :return: Currency quotations for the specified date.
   :rtype: CotizacionFecha
   :raises BCRAApiError: If the API request fails or returns unexpected data.

.. py:method:: get_evolucion_moneda(moneda: str, fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None, limit: int = 1000, offset: int = 0)

   Fetch the evolution of a specific currency's quotation.

   :param moneda: The currency code.
   :type moneda: str
   :param fecha_desde: Start date (format: YYYY-MM-DD), defaults to None.
   :type fecha_desde: Optional[str]
   :param fecha_hasta: End date (format: YYYY-MM-DD), defaults to None.
   :type fecha_hasta: Optional[str]
   :param limit: Maximum number of results to return (10-1000), defaults to 1000.
   :type limit: int
   :param offset: Number of results to skip, defaults to 0.
   :type offset: int
   :return: A list of currency quotations over time.
   :rtype: List[CotizacionFecha]
   :raises BCRAApiError: If the API request fails or returns unexpected data.
   :raises ValueError: If the limit is out of range.

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
   :type fecha: date
   :param valor: The value of the variable.
   :type valor: float

DatosVariable
^^^^^^^^^^^^^

.. py:class:: DatosVariable

   Represents historical data for a variable.

   :param id_variable: The ID of the variable.
   :type id_variable: int
   :param fecha: The date of the data point.
   :type fecha: date
   :param valor: The value of the variable on the given date.
   :type valor: float

Entidad
^^^^^^^

.. py:class:: Entidad

   Represents a financial entity.

   :param codigo_entidad: The entity's code.
   :type codigo_entidad: int
   :param denominacion: The entity's name.
   :type denominacion: str

Cheque
^^^^^^

.. py:class:: Cheque

   Represents a reported check.

   :param numero_cheque: The check number.
   :type numero_cheque: int
   :param denunciado: Whether the check is reported.
   :type denunciado: bool
   :param fecha_procesamiento: The processing date.
   :type fecha_procesamiento: date
   :param denominacion_entidad: The name of the entity.
   :type denominacion_entidad: str
   :param detalles: List of check details.
   :type detalles: List[ChequeDetalle]

Divisa
^^^^^^

.. py:class:: Divisa

   Represents a currency.

   :param codigo: The currency code (ISO).
   :type codigo: str
   :param denominacion: The currency name.
   :type denominacion: str

CotizacionFecha
^^^^^^^^^^^^^^^

.. py:class:: CotizacionFecha

   Represents currency quotations for a specific date.

   :param fecha: The date of the quotations.
   :type fecha: Optional[date]
   :param detalle: List of quotation details.
   :type detalle: List[CotizacionDetalle]

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