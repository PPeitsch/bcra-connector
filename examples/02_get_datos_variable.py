"""
Example showing how to retrieve historical data for specific BCRA variables.
Includes date range handling and time series visualization.
"""

import logging
import os
import sys
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.bcra_connector import BCRAApiError, BCRAConnector

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def save_plot(fig, filename):
    static_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "docs/build/_static/images")
    )
    os.makedirs(static_dir, exist_ok=True)
    filepath = os.path.join(static_dir, filename)
    fig.savefig(filepath)
    logger.info(f"Plot saved as '{filepath}'")


def main():
    connector = BCRAConnector(verify_ssl=False)

    try:
        variable_name = "Reservas Internacionales del BCRA"
        variable = connector.get_variable_by_name(variable_name)

        if not variable:
            logger.error(f"Variable '{variable_name}' not found")
            return

        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        logger.info(
            f"Fetching data for {variable_name} from {start_date.date()} to {end_date.date()}..."
        )
        response_data = connector.get_datos_variable(
            variable.idVariable, start_date, end_date
        )

        # Access the list of data points via response_data.results
        datos_list = response_data.results

        logger.info(f"Found {len(datos_list)} data points.")

        logger.info("Last 5 data points:")
        for dato in datos_list[-5:]:
            logger.info(f"Date: {dato.fecha}, Value: {dato.valor}")

        # Plot the data
        fig, ax = plt.subplots(figsize=(12, 6))

        if not datos_list:  # Check if the list is empty before processing
            logger.warning(f"No data points found for {variable_name} to plot.")
            plt.close(fig)  # Close the empty figure
            return

        # Convert dates and prepare data arrays for matplotlib
        dates = [
            datetime.combine(dato.fecha, datetime.min.time()) for dato in datos_list
        ]
        values = [dato.valor for dato in datos_list]

        dates_array = np.array(dates)
        values_array = np.array(values)

        ax.plot_date(dates_array, values_array, "-")
        ax.set_title(f"{variable_name} - Last 30 Days")
        ax.set_xlabel("Date")
        ax.set_ylabel("Value")
        plt.xticks(rotation=45)
        plt.tight_layout()
        save_plot(fig, f"variable_{variable.idVariable}_data.png")

    except BCRAApiError as e:
        logger.error(f"API Error occurred: {str(e)}")
    except ValueError as e:
        logger.error(f"Value Error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    main()
