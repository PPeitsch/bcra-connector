"""
Example of different BCRA connector configurations (Monetarias v3.0 context).
Demonstrates timeout settings, SSL verification, and debug mode.
"""

import logging
from datetime import datetime, timedelta

from bcra_connector import BCRAApiError, BCRAConnector

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_connection(connector: BCRAConnector, description: str) -> None:
    """Tests basic connectivity and data fetching with the given connector."""
    logger.info(f"\n--- Testing: {description} ---")
    try:
        variables = connector.get_principales_variables()
        logger.info(
            f"Successfully fetched {len(variables)} principal variables/series."
        )
        if not variables:
            logger.warning("No principal variables returned.")
            return

        first_var = variables[0]
        logger.info(
            f"First variable: ID={first_var.idVariable}, Desc='{first_var.descripcion}', Cat='{first_var.categoria}'"
        )

        variable_id_to_test = first_var.idVariable
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        logger.info(f"Fetching data for variable ID {variable_id_to_test}...")
        response_data = connector.get_datos_variable(
            variable_id_to_test, desde=start_date, hasta=end_date, limit=10
        )

        datos_list = response_data.results
        logger.info(
            f"Successfully fetched {len(datos_list)} data points for variable ID {variable_id_to_test}."
        )
        if datos_list:
            latest_point = max(datos_list, key=lambda x: x.fecha)
            logger.info(
                f"  Latest fetched data point: Date: {latest_point.fecha.isoformat()}, Value: {latest_point.valor}"
            )
        else:
            logger.info(
                f"  No data points returned for variable ID {variable_id_to_test} in the specified range/limit."
            )

    except BCRAApiError as e:
        logger.error(f"API Error occurred during '{description}': {str(e)}")
    except ValueError as e:
        logger.error(f"Value Error occurred during '{description}': {str(e)}")
    except Exception as e:
        logger.error(
            f"Unexpected error during '{description}': {str(e)}", exc_info=True
        )


def main() -> None:
    """Main function to demonstrate different connector configurations."""
    logger.info("Starting connector configuration examples...")

    logger.info(
        "\nNOTE: Default connector test (SSL ON) might fail if system certs/proxy are not set up for api.bcra.gob.ar."
    )
    try:
        connector_default = BCRAConnector()
        test_connection(connector_default, "Default connector (SSL verification ON)")
    except BCRAApiError as e:
        logger.error(f"Default connector (SSL ON) API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error with default connector: {e}", exc_info=True)

    logger.info(
        "\nWARNING: The following tests disable SSL verification. This is not recommended for production."
    )
    connector_no_ssl = BCRAConnector(verify_ssl=False)
    test_connection(connector_no_ssl, "Connector with SSL verification disabled")

    connector_debug = BCRAConnector(verify_ssl=False, debug=True)
    test_connection(
        connector_debug, "Connector with SSL verification disabled and debug mode ON"
    )

    connector_en = BCRAConnector(verify_ssl=False, language="en-US", debug=True)
    test_connection(
        connector_en, "Connector with English language (en-US) and debug ON"
    )

    logger.info(
        "\nConnector configuration examples finished. "
        "In a production environment, always prefer SSL verification (verify_ssl=True)."
    )


if __name__ == "__main__":
    main()
