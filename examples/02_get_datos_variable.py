"""
Example showing how to retrieve historical data for specific BCRA variables (Monetarias v4.0).
Includes date range handling, pagination (limit/offset), and time series visualization.
"""

import logging
import os
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np

from bcra_connector import BCRAApiError, BCRAConnector

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def save_plot(fig, filename: str) -> None:
    """Saves the given matplotlib figure to the docs static images directory."""
    static_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "docs/build/_static/images")
    )
    os.makedirs(static_dir, exist_ok=True)
    filepath = os.path.join(static_dir, filename)
    fig.savefig(filepath)
    logger.info(f"Plot saved as '{filepath}'")


def main() -> None:
    """Main function to demonstrate fetching historical data for a variable."""
    connector = BCRAConnector(verify_ssl=False)

    try:
        variable_name_to_fetch = "Reservas Internacionales del BCRA"
        target_variable = connector.get_variable_by_name(variable_name_to_fetch)

        if not target_variable:
            logger.warning(
                f"Variable '{variable_name_to_fetch}' not found by name. Trying first available variable."
            )
            all_variables = connector.get_principales_variables()
            if not all_variables:
                logger.error("No variables found at all. Cannot proceed.")
                return
            target_variable = all_variables[0]
            logger.info(
                f"Using variable ID: {target_variable.idVariable} ({target_variable.descripcion}) for demonstration."
            )

        variable_id_to_use = target_variable.idVariable
        display_variable_name = target_variable.descripcion

        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        limit_param = 50
        offset_param = 0

        logger.info(
            f"Fetching data for '{display_variable_name}' (ID: {variable_id_to_use}) "
            f"from {start_date.date().isoformat()} to {end_date.date().isoformat()} with limit={limit_param}, offset={offset_param}..."
        )

        response_data = connector.get_datos_variable(
            variable_id_to_use,
            desde=start_date,
            hasta=end_date,
            limit=limit_param,
            offset=offset_param,
        )

        datos_list = response_data.results
        metadata = response_data.metadata

        # In v4.0, results is a list of DatosVariable objects, each with a detalle array
        # Flatten all detalle arrays into a single list
        all_data_points = []
        for datos_variable in datos_list:
            all_data_points.extend(datos_variable.detalle)

        logger.info(
            f"Fetched {len(all_data_points)} data points from {len(datos_list)} result groups. "
            f"Total available according to metadata: {metadata.resultset.count}. "
            f"Offset: {metadata.resultset.offset}, Limit: {metadata.resultset.limit}."
        )

        if not all_data_points:
            logger.warning(
                f"No data points returned for '{display_variable_name}'. Cannot plot or show details."
            )
            return

        logger.info("Last 5 data points from the fetched data:")
        for dato in all_data_points[-5:]:
            logger.info(f"  Date: {dato.fecha.isoformat()}, Value: {dato.valor}")

        fig, ax = plt.subplots(figsize=(12, 6))

        dates = [
            datetime.combine(dato.fecha, datetime.min.time())
            for dato in all_data_points
        ]
        values = [dato.valor for dato in all_data_points]

        ax.plot_date(np.array(dates), np.array(values), "-")
        ax.set_title(
            f"'{display_variable_name}\\n(Page with limit={limit_param}, offset={offset_param} in last 90 days)"
        )
        ax.set_xlabel("Date")
        ax.set_ylabel("Value")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        save_plot(fig, f"variable_{variable_id_to_use}_data_v4_paginated.png")

    except BCRAApiError as e:
        logger.error(f"API Error occurred: {str(e)}")
    except ValueError as e:
        logger.error(f"Value Error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
