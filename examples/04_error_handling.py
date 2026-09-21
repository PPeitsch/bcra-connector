"""
Example of proper error handling for common BCRA API scenarios (Monetarias v3.0 context).
Shows how to handle timeouts, rate limits, and API errors.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Type

from bcra_connector import BCRAApiError, BCRAConnector, BCRANotFoundError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_case(
    description: str,
    func: Callable[[], Any],
    expected_exception: Type[BaseException] = Exception,
) -> None:
    """Helper function to run a test case and log results."""
    logger.info(f"\n--- Test case: {description} ---")
    try:
        result = func()
        logger.info(f"Test completed. Result (if any): {result}")
    except expected_exception as e:
        logger.info(f"Expected exception caught: {type(e).__name__}: {str(e)}")
    except Exception as e:
        logger.error(
            f"Unexpected exception raised: {type(e).__name__}: {str(e)} "
            f"(Expected {expected_exception.__name__} or success to not raise)",
            exc_info=True,
        )


def main() -> None:
    """Main function to demonstrate error handling test cases."""
    connector = BCRAConnector(verify_ssl=False, debug=True)

    test_case(
        "Invalid variable ID for monetarias.latest",
        lambda: connector.monetarias.latest(9999999),
        expected_exception=BCRAApiError,
    )

    def invalid_date_order():
        return connector.monetarias.series(
            1, datetime(2023, 1, 10), datetime(2023, 1, 1)
        )

    test_case(
        "Invalid date order (desde > hasta) for monetarias.series",
        invalid_date_order,
        expected_exception=ValueError,
    )

    def malformed_date_string():
        return connector.cambiarias.quotations("12/06/2024")

    test_case(
        "Malformed date string for cambiarias.quotations",
        malformed_date_string,
        expected_exception=ValueError,
    )

    def invalid_limit_low():
        return connector.monetarias.series(1, limit=5)

    test_case(
        "Invalid limit (too low) for monetarias.series",
        invalid_limit_low,
        expected_exception=ValueError,
    )

    def invalid_limit_high():
        return connector.monetarias.series(1, limit=3001)

    test_case(
        "Invalid limit (too high) for monetarias.series",
        invalid_limit_high,
        expected_exception=ValueError,
    )

    def future_date_query():
        today = datetime.now()
        future_start = today + timedelta(days=30)
        future_end = today + timedelta(days=60)
        response = connector.monetarias.series(1, future_start, future_end)
        return f"Results count: {len(response)}"

    test_case(
        "Query with future date range (API behavior test)",
        future_date_query,
        expected_exception=BCRAApiError,
    )

    test_case(
        "Non-existent variable name for monetarias.history",
        lambda: connector.monetarias.history("This Variable Does Not Exist For Sure"),
        expected_exception=ValueError,
    )

    def simulate_api_error_for_datos():
        return connector.monetarias.series(
            9999999, datetime.now() - timedelta(days=1), datetime.now()
        )

    test_case(
        "API error for non-existent ID with monetarias.series",
        simulate_api_error_for_datos,
        expected_exception=BCRAApiError,
    )

    test_case(
        "Invalid currency code for cambiarias.evolution",
        lambda: connector.cambiarias.evolution("XZY"),
        expected_exception=BCRAApiError,
    )

    test_case(
        "Invalid currency pair for cambiarias.pair",
        lambda: connector.cambiarias.pair("XZY", "ABC"),
        expected_exception=BCRAApiError,
    )

    test_case(
        "History for a non-existent variable name",
        lambda: connector.monetarias.history("This Variable Also Does Not Exist"),
        expected_exception=ValueError,
    )

    test_case(
        "Debts for an unknown identification",
        lambda: connector.deudores.debts("20-00000000-0"),
        expected_exception=BCRANotFoundError,
    )

    logger.info("\nError handling example script finished.")


if __name__ == "__main__":
    main()
