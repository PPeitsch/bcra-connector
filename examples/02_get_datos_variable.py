"""
Example showing how to retrieve historical data for specific BCRA variables.
Includes date range handling and time series visualization.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.bcra_connector import BCRAConnector, BCRAApiError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def save_plot(fig, filename):
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs/build/_static/images'))
    os.makedirs(static_dir, exist_ok=True)
    filepath = os.path.join(static_dir, filename)
    fig.savefig(filepath)
    logger.info(f"Plot saved as '{filepath}'")


def main():
    connector = BCRAConnector(verify_ssl=False)  # Set to False only if necessary

    try:
        # Let's get data for Reservas Internacionales del BCRA (usually ID 1)
        variable_name = "Reservas Internacionales del BCRA"
        variable = connector.get_variable_by_name(variable_name)

        if not variable:
            logger.error(f"Variable '{variable_name}' not found")
            return

        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Last 30 days

        logger.info(f"Fetching data for {variable_name} from {start_date.date()} to {end_date.date()}...")
        datos = connector.get_datos_variable(variable.idVariable, start_date, end_date)

        logger.info(f"Found {len(datos)} data points.")
        logger.info("Last 5 data points:")
        for dato in datos[-5:]:
            logger.info(f"Date: {dato.fecha}, Value: {dato.valor}")

        # Plot the data
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot([datetime.strptime(d.fecha, "%Y-%m-%d") for d in datos], [d.valor for d in datos])
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
