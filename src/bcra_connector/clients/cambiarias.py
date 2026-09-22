"""Estadísticas Cambiarias v1.0."""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..estadisticas_cambiarias import CotizacionDetalle, CotizacionFecha, Divisa
from ..exceptions import BCRAApiError
from ..models import DateLike, Page, as_date, resultset
from .base import DomainClient


class CambiariasClient(DomainClient):
    """Currencies, quotations and exchange rates (``connector.cambiarias``)."""

    def currencies(self) -> Page[Divisa]:
        """
        Fetch the list of all currencies.

        :return: A Page of Divisa objects
        :raises BCRAApiError: If the API request fails or returns unexpected data
        """
        self.logger.info("Fetching currencies")
        try:
            data = self._http.request("estadisticascambiarias/v1.0/Maestros/Divisas")
            if "results" not in data or not isinstance(data["results"], list):
                raise BCRAApiError(
                    "Invalid response format for currencies: 'results' key missing or not a list."
                )
            divisas = [Divisa.from_dict(d) for d in data["results"]]
            self.logger.info(f"Successfully fetched {len(divisas)} currencies")
            return Page(divisas, **{"count": len(divisas), **resultset(data)})
        except (KeyError, ValueError) as e:
            raise BCRAApiError(
                f"Unexpected response format or data for divisas: {str(e)}"
            ) from e
        except BCRAApiError:
            raise
        except Exception as e:
            self.logger.exception(f"Unexpected error fetching currencies: {e}")
            raise BCRAApiError(f"Error fetching currencies: {str(e)}") from e

    def quotations(self, fecha: Optional[DateLike] = None) -> CotizacionFecha:
        """
        Fetch currency quotations for a specific date.

        :param fecha: The date for which to fetch quotations, as a ``date``, a
            ``datetime`` or an ISO 8601 string. Defaults to None (latest date).
        :return: A CotizacionFecha object with the quotations
        :raises BCRAApiError: If the API request fails or returns unexpected data
        :raises ValueError: If the date is a string that is not ISO 8601.
        :raises TypeError: If the date is of an unsupported type.
        """
        fecha_date = as_date(fecha, "fecha") if fecha is not None else None
        self.logger.info(
            f"Fetching quotations for date: {fecha_date.isoformat() if fecha_date else 'latest'}"
        )
        try:
            params = {"fecha": fecha_date.isoformat()} if fecha_date else None
            data = self._http.request(
                "estadisticascambiarias/v1.0/Cotizaciones", params
            )
            if "results" not in data or not isinstance(data["results"], dict):
                raise BCRAApiError(
                    "Invalid response format for quotations: 'results' key missing or not a dict."
                )
            cotizacion = CotizacionFecha.from_dict(data["results"])
            fecha_log = (
                cotizacion.fecha.isoformat() if cotizacion.fecha else "latest available"
            )
            self.logger.info(f"Successfully fetched quotations for {fecha_log}")
            return cotizacion
        except (KeyError, ValueError) as e:
            raise BCRAApiError(
                f"Unexpected response format or data for cotizaciones: {str(e)}"
            ) from e
        except BCRAApiError:
            raise
        except Exception as e:
            self.logger.exception(
                f"Unexpected error fetching cotizaciones for {fecha_date}: {e}"
            )
            raise BCRAApiError(
                f"Error fetching quotations for date {fecha_date}: {str(e)}"
            ) from e

    def latest(self) -> Dict[str, float]:
        """
        Get the latest quotations (tipo_cotizacion) for all currencies.

        :return: A dictionary with currency codes as keys and their latest quotations as values.
        :raises BCRAApiError: If fetching quotations fails.
        """
        try:
            cotizaciones = self.quotations()
        except BCRAApiError as e:
            self.logger.error(f"Failed to get latest quotations: {e}")
            raise
        if not cotizaciones or not cotizaciones.detalle:
            self.logger.warning(
                "No quotation details found in the latest API response for quotations."
            )
            return {}
        return {
            detail.codigo_moneda: detail.tipo_cotizacion
            for detail in cotizaciones.detalle
            if detail.codigo_moneda
        }

    def series(
        self,
        moneda: str,
        fecha_desde: Optional[DateLike] = None,
        fecha_hasta: Optional[DateLike] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> Page[CotizacionFecha]:
        """
        Fetch one page of a currency's quotations, as the endpoint returns them.

        For the whole range of the last n days, use :meth:`evolution`.

        :param moneda: The currency code (case-sensitive in URL path).
        :param fecha_desde: Start date, as a ``date``, a ``datetime`` or an ISO 8601
            string. Defaults to None.
        :param fecha_hasta: End date, same types as ``fecha_desde``. Defaults to None.
        :param limit: Maximum number of results to return (10-1000), defaults to 1000.
        :param offset: Number of results to skip, defaults to 0.
        :return: A Page of CotizacionFecha objects with the currency's evolution data.
        :raises BCRAApiError: If the API request fails or returns unexpected data.
        :raises ValueError: If a date is not ISO 8601, the limit is out of range or
            the offset is negative.
        :raises TypeError: If a date is of an unsupported type.
        """
        self.logger.info(f"Fetching evolution for currency: {moneda}")
        desde = as_date(fecha_desde, "fecha_desde") if fecha_desde is not None else None
        hasta = as_date(fecha_hasta, "fecha_hasta") if fecha_hasta is not None else None
        if not (10 <= limit <= 1000):
            raise ValueError("Limit must be between 10 and 1000 for 'evolucion_moneda'")
        if offset < 0:
            raise ValueError("Offset must be non-negative for 'evolucion_moneda'")

        evolucion, total = self._page(moneda, desde, hasta, limit, offset)
        page = Page(evolucion, count=total, offset=offset, limit=limit)
        if page.has_more:
            self.logger.warning(
                f"Returned {len(evolucion)} of {total} quotations for {moneda} "
                f"(offset {offset}). Page with limit/offset, or use "
                f"cambiarias.evolution() to fetch the whole range."
            )
        return page

    def evolution(
        self,
        currency_code: str,
        days: int = 30,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Page[CotizacionFecha]:
        """
        Get the evolution of a currency's quotation for the last n days.

        :param currency_code: The currency code (e.g., 'USD', 'EUR'). Case-sensitive for URL.
        :param days: The number of days to look back, defaults to 30. Must be positive.
        :param limit: Maximum number of results (10-1000). By default (None) the whole
                      range is returned, fetching as many pages as needed.
        :param offset: Number of results to skip, defaults to 0.
        :return: A Page of CotizacionFecha objects.
        :raises ValueError: If days/limit/offset are invalid.
        :raises BCRAApiError: If the API request fails.
        """
        if days <= 0:
            raise ValueError("Number of days must be positive.")
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        if limit is None:
            if offset < 0:
                raise ValueError("Offset must be non-negative.")

            def fetch_page(
                page_limit: int, page_offset: int
            ) -> Tuple[List[CotizacionFecha], Optional[int]]:
                return self._page(
                    currency_code, start_date, end_date, page_limit, page_offset
                )

            rows = self._http.collect_pages(
                fetch_page,
                self._http.config.fx_max_page_size,
                f"{currency_code} quotations",
                start=offset,
            )
            return Page(rows, count=offset + len(rows), offset=offset)

        return self.series(
            currency_code,
            fecha_desde=start_date,
            fecha_hasta=end_date,
            limit=limit,
            offset=offset,
        )

    def pair(
        self, base_currency: str, quote_currency: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get the evolution of a currency pair exchange rate for the last n days.

        ``tasa`` follows the usual ``BASE/QUOTE`` convention: the amount of
        ``quote_currency`` for one unit of ``base_currency`` (``USD/ARS`` ~ 1500
        pesos per dollar, ``EUR/USD`` ~ 1.15 dollars per euro).

        Both currencies are expressed in US dollars on each date: ``USD`` is 1,
        ``ARS`` is ``1 / tipoCotizacion`` of USD, and any other currency is its
        ``tipoPase`` (dollars per unit). Only the series needed are requested, so a
        pair against USD makes one request. Dates where a currency has no usable
        rate (e.g. ``REF``, which has no ``tipoPase``) are skipped with a warning.

        :param base_currency: The base currency code (e.g., 'USD'). Case-insensitive.
        :param quote_currency: The quote currency code (e.g., 'ARS'). Case-insensitive.
        :param days: The number of days to look back, defaults to 30. Must be positive.
        :return: List of dictionaries with 'fecha' (a ``date``) and 'tasa' (exchange
            rate), oldest first.
        :raises ValueError: If days is invalid.
        :raises BCRAApiError: If underlying API calls fail.
        """
        if days <= 0:
            raise ValueError("Number of days must be positive.")
        base_currency = base_currency.upper()
        quote_currency = quote_currency.upper()
        pair = f"{base_currency}/{quote_currency}"

        # Series each currency needs: USD needs none, ARS needs USD's quotation.
        sources = {"USD": None, "ARS": "USD"}
        needed: List[str] = []
        for code in (base_currency, quote_currency):
            source = sources.get(code, code)
            if source and source not in needed:
                needed.append(source)
        if not needed:  # USD/USD: fetch USD just for its dates
            needed.append("USD")

        series: Dict[str, Dict[date, CotizacionDetalle]] = {}
        try:
            for code in needed:
                by_date: Dict[date, CotizacionDetalle] = {}
                for cf in self.evolution(code, days):
                    if not cf.fecha:
                        continue
                    try:
                        by_date[cf.fecha] = self.detalle(cf, code)
                    except ValueError:
                        self.logger.debug(
                            f"{code} not in cotizacion for {cf.fecha.isoformat()}"
                        )
                series[code] = by_date
        except BCRAApiError as e:
            self.logger.error(
                f"Failed to get evolution for currency pair {pair} due to API error: {e}"
            )
            raise

        def usd_per_unit(code: str, day: date) -> float:
            if code == "USD":
                return 1.0
            if code == "ARS":
                ars_per_usd = series["USD"][day].tipo_cotizacion
                return 1.0 / ars_per_usd if ars_per_usd else 0.0
            return series[code][day].tipo_pase

        common_dates = sorted(set.intersection(*(set(s) for s in series.values())))
        pair_evolution = []
        for day in common_dates:
            base_usd = usd_per_unit(base_currency, day)
            quote_usd = usd_per_unit(quote_currency, day)
            if base_usd > 0 and quote_usd > 0:
                pair_evolution.append({"fecha": day, "tasa": base_usd / quote_usd})
            else:
                self.logger.warning(
                    f"No USD rate for {base_currency if base_usd <= 0 else quote_currency} "
                    f"on {day.isoformat()}, skipping {pair}."
                )
        self.logger.info(
            f"Calculated {len(pair_evolution)} data points for {pair} pair evolution."
        )
        return pair_evolution

    @staticmethod
    def detalle(
        cotizacion_fecha: CotizacionFecha, currency_code: str
    ) -> CotizacionDetalle:
        """Pick one currency's detail out of a day's quotations.

        :raises ValueError: If the object is empty or doesn't carry that currency.
        """
        if not cotizacion_fecha or not cotizacion_fecha.detalle:
            raise ValueError(
                f"Invalid or empty CotizacionFecha object provided for currency {currency_code}."
            )
        for detail in cotizacion_fecha.detalle:
            if detail.codigo_moneda == currency_code:
                return detail
        raise ValueError(
            f"Currency {currency_code} not found in cotizacion for date {cotizacion_fecha.fecha.isoformat() if cotizacion_fecha.fecha else 'N/A'}"
        )

    def _page(
        self,
        moneda: str,
        fecha_desde: Optional[date],
        fecha_hasta: Optional[date],
        limit: int,
        offset: int,
    ) -> Tuple[List[CotizacionFecha], Optional[int]]:
        """Fetch one page of a currency's evolution and the total result count."""
        params = {
            k: v
            for k, v in {
                "fechaDesde": fecha_desde.isoformat() if fecha_desde else None,
                "fechaHasta": fecha_hasta.isoformat() if fecha_hasta else None,
                "limit": limit,
                "offset": offset,
            }.items()
            if v is not None
        }

        endpoint = f"estadisticascambiarias/v1.0/Cotizaciones/{moneda}"
        try:
            data = self._http.request(endpoint, params=params if params else None)
            if "results" not in data or not isinstance(data["results"], list):
                raise BCRAApiError(
                    f"Invalid response format for currency evolution ({moneda}): 'results' key missing/invalid."
                )
            evolucion = [CotizacionFecha.from_dict(cf) for cf in data["results"]]
            self.logger.info(
                f"Successfully fetched {len(evolucion)} data points for {moneda}"
            )
            metadata = data.get("metadata")
            count = (
                metadata.get("resultset", {}).get("count")
                if isinstance(metadata, dict)
                else None
            )
            return evolucion, count if isinstance(count, int) else None
        except (KeyError, ValueError) as e:
            raise BCRAApiError(
                f"Unexpected response format or data for {moneda} evolution: {str(e)}"
            ) from e
        except BCRAApiError:
            raise
        except Exception as e:
            self.logger.exception(
                f"Unexpected error fetching evolution for {moneda}: {e}"
            )
            raise BCRAApiError(
                f"Error fetching evolution for {moneda}: {str(e)}"
            ) from e
