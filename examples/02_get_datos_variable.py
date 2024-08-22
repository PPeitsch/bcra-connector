from bcra_connector import BCRAConnector, BCRAApiError
from datetime import datetime, timedelta


def main():
    connector = BCRAConnector()

    try:
        # Let's get data for Reservas Internacionales del BCRA (usually ID 1)
        id_variable = 1
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Last 30 days

        print(f"Fetching data for variable ID {id_variable} from {start_date.date()} to {end_date.date()}...")
        datos = connector.get_datos_variable(id_variable, start_date, end_date)

        print(f"Found {len(datos)} data points.")
        print("\nLast 5 data points:")
        for dato in datos[-5:]:
            print(f"Date: {dato.fecha}, Value: {dato.valor}")
    except BCRAApiError as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
