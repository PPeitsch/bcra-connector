"""
Example of fetching and comparing latest values for multiple BCRA variables.
Demonstrates multi-variable analysis and visualization.
"""

import os
import sys
import logging
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

    # Let's get the latest value for a few different variables
    variable_names = ["Reservas Internacionales del BCRA", "Tipo de Cambio Minorista", "Tasa de Política Monetaria"]

    latest_values = []
    for variable_name in variable_names:
        try:
            logger.info(f"Fetching latest value for '{variable_name}'...")
            variable = connector.get_variable_by_name(variable_name)
            if not variable:
                logger.warning(f"Variable '{variable_name}' not found")
                continue

            latest = connector.get_latest_value(variable.idVariable)
            logger.info(f"Latest value: {latest.valor} ({latest.fecha})")
            latest_values.append((variable_name, latest.valor))
        except BCRAApiError as e:
            logger.error(f"API Error for '{variable_name}': {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error for '{variable_name}': {str(e)}")

    # Plot the latest values
    if latest_values:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar([name for name, _ in latest_values], [value for _, value in latest_values])
        ax.set_title("Latest Values for Different Variables")
        ax.set_xlabel("Variable")
        ax.set_ylabel("Value")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        save_plot(fig, "latest_values.png")
    else:
        logger.warning("No data to plot")


if __name__ == "__main__":
    main()
