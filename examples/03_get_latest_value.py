import os
import sys
import logging
from bcra_connector import BCRAConnector, BCRAApiError
import matplotlib.pyplot as plt

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def save_plot(fig, filename):
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs/build/_static/images'))
    os.makedirs(static_dir, exist_ok=True)
    filepath = os.path.join(static_dir, filename)
    fig.savefig(filepath)
    logger.info(f"Plot saved as '{filepath}'")

def main():
    connector = BCRAConnector()

    # Let's get the latest value for a few different variables
    variable_ids = [1, 4, 5]  # Example variable IDs

    latest_values = []
    for id_variable in variable_ids:
        try:
            logger.info(f"Fetching latest value for variable ID {id_variable}...")
            latest = connector.get_latest_value(id_variable)
            logger.info(f"Latest value: {latest.valor} ({latest.fecha})")
            latest_values.append((id_variable, latest.valor))
        except BCRAApiError as e:
            logger.error(f"Error occurred with SSL verification: {str(e)}")
            logger.info("Retrying without SSL verification...")
            connector = BCRAConnector(verify_ssl=False)
            try:
                latest = connector.get_latest_value(id_variable)
                logger.info(f"Latest value: {latest.valor} ({latest.fecha})")
                latest_values.append((id_variable, latest.valor))
            except BCRAApiError as e:
                logger.error(f"Error occurred even without SSL verification: {str(e)}")

    # Plot the latest values
    if latest_values:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar([f"Variable {id}" for id, _ in latest_values], [value for _, value in latest_values])
        ax.set_title("Latest Values for Different Variables")
        ax.set_xlabel("Variable ID")
        ax.set_ylabel("Value")
        plt.tight_layout()
        save_plot(fig, "latest_values.png")

if __name__ == "__main__":
    main()
