import os
import sys
import logging
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bcra_connector import BCRAConnector, BCRAApiError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_case(description, func):
    logger.info(f"\nTest case: {description}")
    try:
        func()
        logger.info("Test passed without raising an exception")
    except Exception as e:
        logger.info(f"Exception raised: {type(e).__name__}: {str(e)}")

def main():
    connector = BCRAConnector(verify_ssl=False)  # Set to False for testing purposes

    # Test case 1: Invalid variable ID
    test_case("Invalid variable ID", lambda: connector.get_latest_value(99999))

    # Test case 2: Invalid date range
    def invalid_date_range():
        end_date = datetime.now()
        start_date = end_date - timedelta(days=366)  # More than 1 year
        connector.get_datos_variable(1, start_date, end_date)
    test_case("Invalid date range", invalid_date_range)

    # Test case 3: Future date
    def future_date():
        future_date = datetime.now() + timedelta(days=30)
        connector.get_datos_variable(1, datetime.now(), future_date)
    test_case("Future date", future_date)

    # Test case 4: Non-existent variable name
    test_case("Non-existent variable name", lambda: connector.get_variable_by_name("Non-existent Variable"))

    # Test case 5: API error simulation
    def simulate_api_error():
        # This assumes that ID -1 will cause an API error. Adjust if necessary.
        connector.get_datos_variable(-1, datetime.now() - timedelta(days=30), datetime.now())
    test_case("API error simulation", simulate_api_error)

if __name__ == "__main__":
    main()
