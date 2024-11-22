"""
Example demonstrating how to fetch and analyze principal variables from BCRA.
Shows basic usage, error handling, and data visualization.
"""

import logging
import os
import sys

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
        logger.info("Fetching principal variables...")
        variables = connector.get_principales_variables()
        logger.info(f"Found {len(variables)} variables.")
        logger.info("First 5 variables:")
        for var in variables[:5]:
            logger.info(f"ID: {var.idVariable}, Description: {var.descripcion}")
            logger.info(f"  Latest value: {var.valor} ({var.fecha})")

        # Plot the first 10 variables
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar([var.descripcion[:20] for var in variables[:10]], [var.valor for var in variables[:10]])
        ax.set_title("Top 10 Principal Variables")
        ax.set_xlabel("Variables")
        ax.set_ylabel("Value")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        save_plot(fig, "principal_variables.png")

        # Example of using the utility method
        variable_name = "Reservas Internacionales del BCRA"
        try:
            history = connector.get_variable_history(variable_name, days=30)
            logger.info(f"Historical data for {variable_name}:")
            for data_point in history[-5:]:  # Show last 5 data points
                logger.info(f"  {data_point.fecha}: {data_point.valor}")
        except ValueError as e:
            logger.error(f"Error fetching variable history: {str(e)}")

    except BCRAApiError as e:
        logger.error(f"API Error occurred: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    main()
