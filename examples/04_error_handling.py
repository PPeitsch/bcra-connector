"""
Example of proper error handling for common BCRA API scenarios.
Shows how to handle timeouts, rate limits, and API errors.
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.bcra_connector import BCRAConnector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_case(description, func):
    logger.info(f"\nTest case: {description}")
    try:
        result = func()
        logger.info(f"Test passed. Result: {result}")
    except Exception as e:
        logger.error(f"Exception raised: {type(e).__name__}: {str(e)}")


def main():
    connector = BCRAConnector(verify_ssl=False)  # Set to False for testing purposes

    # Test case 1: Invalid variable ID
    test_case("Invalid variable ID", lambda: connector.get_latest_value(99999))

    # Test case 2: Invalid date range
    def invalid_date_range():
        end_date = datetime.now()
        start_date = end_date - timedelta(days=366)  # More than 1 year
        return connector.get_datos_variable(1, start_date, end_date)

    test_case("Invalid date range", invalid_date_range)

    # Test case 3: Future date
    def future_date():
        future_date = datetime.now() + timedelta(days=30)
        return connector.get_datos_variable(1, datetime.now(), future_date)

    test_case("Future date", future_date)

    # Test case 4: Non-existent variable name
    test_case("Non-existent variable name", lambda: connector.get_variable_by_name("Non-existent Variable"))

    # Test case 5: API error simulation
    def simulate_api_error():
        # This assumes that ID -1 will cause an API error. Adjust if necessary.
        return connector.get_datos_variable(-1, datetime.now() - timedelta(days=30), datetime.now())

    test_case("API error simulation", simulate_api_error)

    # Test case 6: Get currency evolution with invalid currency code
    test_case("Invalid currency code", lambda: connector.get_currency_evolution("INVALID"))

    # Test case 7: Get currency pair evolution with invalid currency codes
    test_case("Invalid currency pair", lambda: connector.get_currency_pair_evolution("INVALID1", "INVALID2"))

    # Test case 8: Generate report for non-existent variable
    test_case("Generate report for non-existent variable",
              lambda: connector.generate_variable_report("Non-existent Variable"))

    # Test case 9: Get correlation between non-existent variables
    test_case("Correlation between non-existent variables",
              lambda: connector.get_variable_correlation("Non-existent Variable 1", "Non-existent Variable 2"))


if __name__ == "__main__":
    main()
