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

    try:
        logger.info("Fetching principal variables...")
        variables = connector.get_principales_variables()
    except BCRAApiError as e:
        logger.error(f"Error occurred with SSL verification: {str(e)}")
        logger.info("Retrying without SSL verification...")
        connector = BCRAConnector(verify_ssl=False)
        try:
            variables = connector.get_principales_variables()
        except BCRAApiError as e:
            logger.error(f"Error occurred even without SSL verification: {str(e)}")
            return

    logger.info(f"Found {len(variables)} variables.")
    logger.info("First 5 variables:")
    for var in variables[:5]:
        logger.info(f"ID: {var.id_variable}, Description: {var.descripcion}")
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

if __name__ == "__main__":
    main()
