"""
Example of different BCRA connector configurations.
Demonstrates timeout settings, SSL verification, and debug mode.
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.bcra_connector import BCRAConnector, BCRAApiError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_connection(connector, description):
    logger.info(f"\n{description}:")
    try:
        # Fetch principal variables
        variables = connector.get_principales_variables()
        logger.info(f"Successfully fetched {len(variables)} principal variables.")
        if variables:
            logger.info(f"First variable: {variables[0].descripcion}")

        # Fetch data for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # Assuming ID 1 is for international reserves
        data = connector.get_datos_variable(1, start_date, end_date)
        logger.info(f"Successfully fetched {len(data)} data points.")
        if data:
            logger.info(f"Latest data point: Date: {data[-1].fecha}, Value: {data[-1].valor}")
    except BCRAApiError as e:
        logger.error(f"API Error occurred: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")


def main():
    # Default usage (SSL verification enabled)
    logger.warning("Testing with SSL verification enabled (this may fail if the certificate cannot be verified)")
    connector_default = BCRAConnector()
    test_connection(connector_default, "Default connector (SSL verification enabled)")

    # SSL verification disabled
    logger.warning(
        "\nWARNING: The following tests disable SSL verification. This is not recommended for production use.")
    connector_no_ssl = BCRAConnector(verify_ssl=False)
    test_connection(connector_no_ssl, "Connector with SSL verification disabled")

    # SSL verification disabled and debug mode on
    connector_debug = BCRAConnector(verify_ssl=False, debug=True)
    test_connection(connector_debug, "Connector with SSL verification disabled and debug mode on")

    # Different language setting
    connector_en = BCRAConnector(verify_ssl=False, language="en-US")
    test_connection(connector_en, "Connector with English language setting")

    logger.warning(
        "\nNOTE: In a production environment, always use SSL verification unless you have a specific reason not to.")


if __name__ == "__main__":
    main()
