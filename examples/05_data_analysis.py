from bcra_connector import BCRAConnector
from datetime import datetime, timedelta
import matplotlib.pyplot as plt


def main():
    connector = BCRAConnector()

    # Let's analyze Reservas Internacionales del BCRA (usually ID 1)
    id_variable = 1
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # Last year

    print(f"Fetching data for variable ID {id_variable} from {start_date.date()} to {end_date.date()}...")
    datos = connector.get_datos_variable(id_variable, start_date, end_date)

    dates = [datetime.strptime(dato.fecha, "%Y-%m-%d") for dato in datos]
    values = [dato.valor for dato in datos]

    plt.figure(figsize=(12, 6))
    plt.plot(dates, values)
    plt.title(f"Variable ID {id_variable} - Last Year")
    plt.xlabel("Date")
    plt.ylabel("Value")
    plt.grid(True)
    plt.savefig("variable_analysis.png")
    plt.close()

    print(f"Analysis plot saved as 'variable_analysis.png'")

    # Simple statistics
    print(f"\nSimple statistics:")
    print(f"Number of data points: {len(datos)}")
    print(f"Minimum value: {min(values)}")
    print(f"Maximum value: {max(values)}")
    print(f"Average value: {sum(values) / len(values):.2f}")


if __name__ == "__main__":
    main()
