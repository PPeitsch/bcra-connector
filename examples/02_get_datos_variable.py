from bcra_connector import BCRAConnector, BCRAApiError
from datetime import datetime, timedelta
import matplotlib.pyplot as plt


def main():
    connector = BCRAConnector()

    # Let's get data for Reservas Internacionales del BCRA (usually ID 1)
    id_variable = 1
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # Last 30 days

    try:
        print(f"Fetching data for variable ID {id_variable} from {start_date.date()} to {end_date.date()}...")
        datos = connector.get_datos_variable(id_variable, start_date, end_date)
    except BCRAApiError as e:
        print(f"Error occurred with SSL verification: {str(e)}")
        print("Retrying without SSL verification...")
        connector = BCRAConnector(verify_ssl=False)
        try:
            datos = connector.get_datos_variable(id_variable, start_date, end_date)
        except BCRAApiError as e:
            print(f"Error occurred even without SSL verification: {str(e)}")
            return

    print(f"Found {len(datos)} data points.")
    print("\nLast 5 data points:")
    for dato in datos[-5:]:
        print(f"Date: {dato.fecha}, Value: {dato.valor}")

    # Plot the data
    plt.figure(figsize=(12, 6))
    plt.plot([datetime.strptime(d.fecha, "%Y-%m-%d") for d in datos], [d.valor for d in datos])
    plt.title(f"Variable ID {id_variable} - Last 30 Days")
    plt.xlabel("Date")
    plt.ylabel("Value")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"variable_{id_variable}_data.png")
    print(f"Plot saved as 'variable_{id_variable}_data.png'")


if __name__ == "__main__":
    main()
