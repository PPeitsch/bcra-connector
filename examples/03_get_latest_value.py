import logging
from bcra_connector import BCRAConnector, BCRAApiError
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
        plt.figure(figsize=(10, 6))
        plt.bar([f"Variable {id}" for id, _ in latest_values], [value for _, value in latest_values])
        plt.title("Latest Values for Different Variables")
        plt.xlabel("Variable ID")
        plt.ylabel("Value")
        plt.tight_layout()
        plt.savefig("latest_values.png")
        logger.info("Plot saved as 'latest_values.png'")


if __name__ == "__main__":
    main()
