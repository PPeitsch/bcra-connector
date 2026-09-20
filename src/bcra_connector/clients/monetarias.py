"""Principales Variables / Monetarias v4.0."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..exceptions import BCRAApiError
from ..models import DateLike, Page, as_date, resultset
from ..principales_variables import (
    DatosVariable,
    DetalleMonetaria,
    PrincipalesVariables,
)
from .base import DomainClient


class MonetariasClient(DomainClient):
    """Monetary series and principal variables (``connector.monetarias``)."""

    def list(self) -> Page[PrincipalesVariables]:
        """
        Fetch the list of all monetary series and principal variables (API v4.0).

        Pages through the whole catalog, so the page holds every series.

        :return: A Page of PrincipalesVariables objects with extended metadata
        :raises BCRAApiError: If the API request fails or returns unexpected data
        """
        self.logger.info("Fetching monetary series and principal variables (v4.0)")
        try:

            def fetch_page(limit: int, offset: int) -> Tuple[List[Any], Optional[int]]:
                data = self._http.request(
                    "estadisticas/v4.0/Monetarias", {"Limit": limit, "Offset": offset}
                )
                if not isinstance(data.get("results"), list):
                    raise BCRAApiError(
                        "Unexpected response format: 'results' is not a list or missing"
                    )
                # In this endpoint resultset.count is the number of results from the
                # offset on, not the total: only a short page ends the listing.
                return data["results"], None

            raw_results = self._http.collect_pages(
                fetch_page, self._page_size(), "the variables catalog"
            )

            variables = []
            for item in raw_results:
                try:
                    variables.append(PrincipalesVariables.from_dict(item))
                except (ValueError, KeyError) as e:
                    self.logger.warning(
                        f"Skipping invalid variable data: {e} - Data: {item}"
                    )

            if not variables and raw_results:  # results existed but parsing failed
                self.logger.error(
                    "Failed to parse any variable data despite receiving results."
                )
            elif not variables:
                self.logger.warning("No valid variables found in the response")
            else:
                self.logger.info(
                    f"Successfully fetched and parsed {len(variables)} variables (v4.0)"
                )
            return Page(variables, count=len(variables))
        except BCRAApiError:
            raise
        except Exception as e:
            error_msg = f"Error fetching principal variables (v4.0): {str(e)}"
            self.logger.exception(error_msg)
            raise BCRAApiError(error_msg) from e

    def series(
        self,
        id_variable: int,
        desde: Optional[DateLike] = None,
        hasta: Optional[DateLike] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Page[DatosVariable]:
        """
        Fetch the list of values for a variable/series (API v4.0).

        Uses pagination via limit and offset. If desde/hasta are omitted, API defaults apply.

        :param id_variable: The ID of the desired variable. Case-sensitive `{IdVariable}` in URL path.
        :param desde: The start date of the range to query (inclusive). Optional.
            A ``date``, a ``datetime`` or an ISO 8601 string.
        :param hasta: The end date of the range to query (inclusive). Optional.
            Same types as ``desde``.
        :param limit: Maximum number of results (10-3000). Optional, API defaults to 1000.
        :param offset: Number of results to skip for pagination. Optional, defaults to 0.
        :return: A Page of DatosVariable objects, each with its ``detalle`` data points.
            Careful with the page's metadata on this endpoint: ``count`` is the number
            of *data points* the API reports, while the page holds *groups* of them, so
            ``len(page)`` and ``count`` are not in the same unit. ``has_more`` still
            answers what it should — whether data is left past this page.
        :raises ValueError: If a date is not ISO 8601, the range is invalid, or
            limit/offset are out of bounds.
        :raises TypeError: If a date is of an unsupported type.
        :raises BCRAApiError: If the API request fails.
        """
        desde_date = as_date(desde, "desde") if desde is not None else None
        hasta_date = as_date(hasta, "hasta") if hasta is not None else None

        log_msg_parts = [f"Fetching data for variable {id_variable}"]
        if desde_date:
            log_msg_parts.append(f"from {desde_date.isoformat()}")
        if hasta_date:
            log_msg_parts.append(f"to {hasta_date.isoformat()}")
        if limit is not None:
            log_msg_parts.append(f"limit {limit}")
        if offset is not None:
            log_msg_parts.append(f"offset {offset}")
        self.logger.info(" ".join(log_msg_parts) + " (v4.0)")

        if desde_date and hasta_date and desde_date > hasta_date:
            raise ValueError(
                "'desde' date must be earlier than or equal to 'hasta' date"
            )
        if limit is not None and not (10 <= limit <= 3000):
            raise ValueError("Limit must be between 10 and 3000")
        if offset is not None and offset < 0:
            raise ValueError("Offset must be non-negative")

        params: Dict[str, Any] = {}
        if desde_date:
            params["Desde"] = desde_date.isoformat()
        if hasta_date:
            params["Hasta"] = hasta_date.isoformat()
        if limit is not None:
            params["Limit"] = limit
        if offset is not None:
            params["Offset"] = offset

        endpoint = f"estadisticas/v4.0/Monetarias/{id_variable}"

        try:
            raw_api_data = self._http.request(
                endpoint, params=params if params else None
            )
            if not isinstance(raw_api_data.get("results"), list):
                raise ValueError("Missing or invalid 'results' in the response")
            page: Page[DatosVariable] = Page(
                [DatosVariable.from_dict(item) for item in raw_api_data["results"]],
                **resultset(raw_api_data),
            )
            # Count total data points across all results
            total_points = sum(len(r.detalle) for r in page)
            self.logger.info(
                f"Successfully fetched and parsed {total_points} data points "
                f"(total available: {page.count}) for variable {id_variable} (v4.0)"
            )
            return page
        except (ValueError, KeyError) as e:
            error_msg = f"Error parsing response for variable {id_variable} (v4.0): {e}"
            self.logger.exception(error_msg)
            raise BCRAApiError(error_msg) from e
        except BCRAApiError:
            self.logger.error(
                f"API Error fetching data for variable {id_variable} (v4.0)"
            )
            raise
        except Exception as e:
            error_msg = (
                f"Unexpected error fetching data for variable {id_variable} (v4.0): {e}"
            )
            self.logger.exception(error_msg)
            raise BCRAApiError(error_msg) from e

    def latest(self, id_variable: int) -> DetalleMonetaria:
        """
        Fetch the latest value for a specific variable using API v4.0.

        :param id_variable: The ID of the desired variable.
        :return: The latest data point (DetalleMonetaria object) for the specified variable.
        :raises BCRAApiError: If the API request fails or if no data is available.
        """
        self.logger.info(
            f"Fetching latest value for variable {id_variable} (using v4.0 logic)"
        )
        response_data = self.series(id_variable, limit=10)  # Small limit for efficiency

        # Collect all data points from all results
        all_detalles: List[DetalleMonetaria] = []
        for result in response_data:
            all_detalles.extend(result.detalle)

        if not all_detalles:
            # Fallback: If no data with small limit, query last 30 days.
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            self.logger.info(
                f"No recent data found for {id_variable} with limit=10, checking last 30 days."
            )
            # Use a limit that comfortably covers a month of daily data. Note we must
            # NOT reuse metadata.resultset.limit here: it reflects the previous limit=10
            # call and would cap the fallback query at 10 results.
            effective_limit = 100
            response_data = self.series(
                id_variable, desde=start_date, hasta=end_date, limit=effective_limit
            )
            # Collect all data points again
            all_detalles = []
            for result in response_data:
                all_detalles.extend(result.detalle)

            if not all_detalles:
                raise BCRAApiError(
                    f"No data available for variable {id_variable} in the last 30 days."
                )

        latest = max(all_detalles, key=lambda x: x.fecha)
        self.logger.info(
            f"Latest value for variable {id_variable}: {latest.valor} ({latest.fecha.isoformat()})"
        )
        return latest

    def find(self, variable_name: str) -> Optional[PrincipalesVariables]:
        """
        Find a principal variable or monetary series by its name (Monetarias v4.0 API).

        The search is case-insensitive. A description equal to ``variable_name`` wins;
        otherwise the first description containing it is returned, and a warning lists
        the other candidates when there is more than one.

        :param variable_name: The name of the variable/series to find.
        :return: A PrincipalesVariables object if found, None otherwise.
        :raises BCRAApiError: If the variables catalog cannot be fetched.

        The catalog is reused across lookups for ``CATALOG_CACHE_TTL`` seconds; call
        ``clear_cache()`` to force a refetch.
        """
        variables = self._http.cached("variables", self.list)
        normalized_name = variable_name.lower().strip()

        matches = [
            v
            for v in variables
            if v.descripcion and normalized_name in v.descripcion.lower()
        ]
        if not matches:
            self.logger.info(
                f"Variable/series with name containing '{variable_name}' not found."
            )
            return None

        for variable in matches:
            if variable.descripcion and variable.descripcion.lower().strip() == (
                normalized_name
            ):
                return variable

        if len(matches) > 1:
            shown = 10
            candidates = "; ".join(
                f"{v.id_variable}: {v.descripcion}" for v in matches[:shown]
            )
            more = f" (and {len(matches) - shown} more)" if len(matches) > shown else ""
            self.logger.warning(
                f"{len(matches)} variables match '{variable_name}'; returning "
                f"{matches[0].id_variable}. Use a more specific name or the id. "
                f"Candidates: {candidates}{more}"
            )
        return matches[0]

    def history(
        self,
        variable_name: str,
        days: int = 30,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Page[DetalleMonetaria]:
        """
        Get the historical data for a variable/series by name for the last n days (Monetarias v4.0).

        This method returns a flat list of data points for convenience.

        :param variable_name: The name of the variable/series.
        :param days: The number of days to look back, defaults to 30. Must be positive.
        :param limit: Maximum number of results (10-3000). Optional.
        :param offset: Number of results to skip for pagination. Optional.
        :return: A Page of DetalleMonetaria objects. Without ``limit`` and ``offset``
                 it covers the whole range, fetching as many pages as needed.
        :raises ValueError: If the variable is not found or days/limit/offset are invalid.
        :raises BCRAApiError: If the API request fails.
        """
        variable = self.find(variable_name)
        if not variable:
            raise ValueError(f"Variable '{variable_name}' not found")
        if days <= 0:
            raise ValueError("Number of days must be positive.")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        if limit is None and offset is None:

            def fetch_page(
                page_limit: int, page_offset: int
            ) -> Tuple[List[DetalleMonetaria], Optional[int]]:
                page = self.series(
                    variable.id_variable,
                    desde=start_date,
                    hasta=end_date,
                    limit=page_limit,
                    offset=page_offset,
                )
                points = [d for r in page for d in r.detalle]
                return points, page.count

            rows = self._http.collect_pages(
                fetch_page, self._page_size(), f"variable {variable.id_variable}"
            )
            return Page(rows, count=len(rows))

        response_obj = self.series(
            variable.id_variable,
            desde=start_date,
            hasta=end_date,
            limit=limit,
            offset=offset,
        )
        # Flatten the results - extract all DetalleMonetaria from all DatosVariable
        all_detalles: List[DetalleMonetaria] = []
        for result in response_obj:
            all_detalles.extend(result.detalle)
        return Page(
            all_detalles,
            count=response_obj.count,
            offset=response_obj.offset,
            limit=response_obj.limit,
        )

    def _page_size(self) -> int:
        """The largest page the Monetarias endpoints accept."""
        return self._http.config().max_page_size
