"""
Example demonstrating the Exchange Statistics (Estadísticas Cambiarias) API module.
Shows how to fetch currencies, quotations, and evolutions.
"""

import logging
import os

import matplotlib.pyplot as plt

from bcra_connector import BCRAApiError, BCRAConnector

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def save_plot(fig, filename: str) -> None:
    """Saves the given matplotlib figure to the docs static images directory."""
    static_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "docs/build/_static/images")
    )
    os.makedirs(static_dir, exist_ok=True)
    filepath = os.path.join(static_dir, filename)
    fig.savefig(filepath)
    logger.info(f"Plot saved as '{filepath}'")


def main():
    """Main function to demonstrate Exchange Statistics API."""
    connector = BCRAConnector(verify_ssl=False)

    try:
        # 1. Get Currencies
        logger.info("Fetching available currencies...")
        currencies = connector.get_divisas()
        logger.info(f"Found {len(currencies)} currencies.")

        logger.info("First 5 currencies:")
        for curr in currencies[:5]:
            logger.info(f"  Code: {curr.codigo}, Name: {curr.denominacion}")

        # 2. Get Latest Quotations
        logger.info("Fetching latest quotations...")
        quotations = connector.get_cotizaciones()
        date_str = quotations.fecha.isoformat() if quotations.fecha else "Unknown Date"
        logger.info(f"Quotations for date: {date_str}")

        logger.info("First 5 quotations:")
        for detail in quotations.detalle[:5]:
            logger.info(
                f"  {detail.codigo_moneda} ({detail.descripcion}): {detail.tipo_cotizacion}"
            )

        # 3. Evolution of USD
        target_currency = "USD"
        days_to_fetch = 30
        logger.info(
            f"Fetching evolution of {target_currency} for last {days_to_fetch} days..."
        )

        try:
            usd_evolution = connector.get_currency_evolution(
                target_currency, days=days_to_fetch
            )

            dates = []
            values = []

            for c in usd_evolution:
                if c.fecha:
                    # Find the specific currency detail in the list
                    for d in c.detalle:
                        if d.codigo_moneda == target_currency:
                            dates.append(c.fecha)
                            values.append(d.tipo_cotizacion)
                            break

            if dates:
                # Sort by date just in case
                sorted_pairs = sorted(zip(dates, values))
                dates_list, values_list = zip(*sorted_pairs)

                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(list(dates_list), list(values_list), marker="o", linestyle="-")
                ax.set_title(f"{target_currency} Evolution (Last {days_to_fetch} Days)")
                ax.set_xlabel("Date")
                ax.set_ylabel("Rate (ARS)")
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                save_plot(fig, "usd_evolution.png")
            else:
                logger.warning(f"No data points found for {target_currency} evolution.")

        except BCRAApiError as e:
            logger.error(f"Failed to fetch evolution: {e}")

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
