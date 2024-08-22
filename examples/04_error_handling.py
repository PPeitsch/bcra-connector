from bcra_connector import BCRAConnector, BCRAApiError
from datetime import datetime, timedelta


def main():
    connector = BCRAConnector()

    # Test case 1: Invalid variable ID
    try:
        connector.get_latest_value(99999)  # Assuming this ID doesn't exist
    except BCRAApiError as e:
        print(f"Expected error occurred: {e}")

    # Test case 2: Invalid date range
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=366)  # More than 1 year
        connector.get_datos_variable(1, start_date, end_date)
    except ValueError as e:
        print(f"Expected error occurred: {e}")

    # Test case 3: Future date
    try:
        future_date = datetime.now() + timedelta(days=30)
        connector.get_datos_variable(1, datetime.now(), future_date)
    except BCRAApiError as e:
        print(f"Expected error occurred: {e}")


if __name__ == "__main__":
    main()
