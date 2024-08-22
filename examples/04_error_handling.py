import logging
from bcra_connector import BCRAConnector
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_case(description, func):
    logger.info(f"\nTest case: {description}")
    try:
        func()
        logger.warning("Unexpected success")
    except Exception as e:
        logger.info(f"Expected error occurred: {type(e).__name__}: {str(e)}")


def main():
    connector = BCRAConnector(verify_ssl=False)  # Using verify_ssl=False to avoid SSL issues

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

    # Test case 4: Invalid language
    test_case("Invalid language", lambda: BCRAConnector(language="invalid"))


if __name__ == "__main__":
    main()
