import os
import sys
import logging
from bcra_connector import BCRAConnector, BCRAApiError
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def save_plot(fig, filename):
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs/build/_static/images'))
    os.makedirs(static_dir, exist_ok=True)
    filepath = os.path.join(static_dir, filename)
    fig.savefig(filepath)
    logger.info(f"Plot saved as '{filepath}'")

def main():
    connector = BCRAConnector()

    # Let's get data for Reservas Internacionales del BCRA (usually ID 1)
    id_variable = 1
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # Last 30 days

    try:
        logger.info(f"Fetching data for variable ID {id_variable} from {start_date.date()} to {end_date.date()}...")
        datos = connector.get_datos_variable(id_variable, start_date, end_date)
    except BCRAApiError as e:
        logger.error(f"Error occurred with SSL verification: {str(e)}")
        logger.info("Retrying without SSL verification...")
        connector = BCRAConnector(verify_ssl=False)
        try:
            datos = connector.get_datos_variable(id_variable, start_date, end_date)
        except BCRAApiError as e:
            logger.error(f"Error occurred even without SSL verification: {str(e)}")
            return

    logger.info(f"Found {len(datos)} data points.")
    logger.info("Last 5 data points:")
    for dato in datos[-5:]:
        logger.info(f"Date: {dato.fecha}, Value: {dato.valor}")

    # Plot the data
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot([datetime.strptime(d.fecha, "%Y-%m-%d") for d in datos], [d.valor for d in datos])
    ax.set_title(f"Variable ID {id_variable} - Last 30 Days")
    ax.set_xlabel("Date")
    ax.set_ylabel("Value")
    plt.xticks(rotation=45)
    plt.tight_layout()
    save_plot(fig, f"variable_{id_variable}_data.png")

if __name__ == "__main__":
    main()
