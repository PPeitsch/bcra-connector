import os
import sys
import logging
from bcra_connector import BCRAConnector, BCRAApiError
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_connection(connector, description):
    logger.info(f"\n{description}:")
    try:
        # Fetch data for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # Assuming ID 1 is for international reserves
        data = connector.get_datos_variable(1, start_date, end_date)
        logger.info(f"Successfully fetched {len(data)} data points.")
        if data:
            logger.info(f"Latest data point: Date: {data[-1].fecha}, Value: {data[-1].valor}")
    except BCRAApiError as e:
        logger.error(f"Error occurred: {str(e)}")

def main():
    # Default usage (SSL verification enabled)
    connector_default = BCRAConnector()
    test_connection(connector_default, "Default connector (SSL verification enabled)")

    # SSL verification disabled
    connector_no_ssl = BCRAConnector(verify_ssl=False)
    test_connection(connector_no_ssl, "Connector with SSL verification disabled")

    # SSL verification disabled and debug mode on
    connector_debug = BCRAConnector(verify_ssl=False, debug=True)
    test_connection(connector_debug, "Connector with SSL verification disabled and debug mode on")

    # Different language setting
    connector_en = BCRAConnector(verify_ssl=False, language="en-US")
    test_connection(connector_en, "Connector with English language setting")

if __name__ == "__main__":
    main()
