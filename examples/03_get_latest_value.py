"""
Example of fetching and comparing latest values for multiple BCRA variables (Monetarias v4.0).
Demonstrates multi-variable analysis and visualization.
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


def main() -> None:
    """Main function to demonstrate fetching latest values."""
    connector = BCRAConnector(verify_ssl=False)

    variable_names_to_check = [
        "Reservas Internacionales del BCRA",
        "Base Monetaria",
    ]

    try:
        all_variables = connector.get_principales_variables()
        if not all_variables:
            logger.error("No variables returned from API. Cannot get latest values.")
            return

        current_variable_names = []
        for name_to_check in variable_names_to_check:
            if any(
                name_to_check.lower() in v.descripcion.lower() for v in all_variables
            ):
                current_variable_names.append(name_to_check)
            else:
                logger.warning(
                    f"Predefined variable '{name_to_check}' not found in API results."
                )

        if not current_variable_names:
            logger.info("Using first few available distinct variables for example.")
            seen_ids = set()
            for v_api in all_variables:
                if v_api.idVariable not in seen_ids:
                    current_variable_names.append(v_api.descripcion)
                    seen_ids.add(v_api.idVariable)
                if len(current_variable_names) >= 3:  # Limit to 3 for example
                    break

        if not current_variable_names:
            logger.error(
                "Could not determine any variables to check for latest values."
            )
            return

    except BCRAApiError as e:
        logger.error(f"Could not fetch variable list to select examples: {e}")
        return
    except Exception as e:
        logger.error(f"Unexpected error fetching variable list: {e}", exc_info=True)
        return

    latest_values_data = []
    for name_or_desc in current_variable_names:
        try:
            logger.info(f"Fetching latest value for '{name_or_desc}'...")
            variable_obj = connector.get_variable_by_name(name_or_desc)

            if not variable_obj:
                logger.warning(
                    f"Variable '{name_or_desc}' not found by name during latest value fetch."
                )
                continue

            # v4.0: get_latest_value() returns DetalleMonetaria (not DatosVariable)
            latest_data_point = connector.get_latest_value(variable_obj.idVariable)
            logger.info(
                f"  ID: {variable_obj.idVariable}, Value: {latest_data_point.valor}, "
                f"Date: {latest_data_point.fecha.isoformat()}, Category: {getattr(variable_obj, 'categoria', 'N/A')}"
            )
            latest_values_data.append(
                (variable_obj.descripcion, latest_data_point.valor)
            )
        except BCRAApiError as e:
            logger.error(f"API Error for '{name_or_desc}': {str(e)}")
        except ValueError as e:
            logger.error(f"Value Error for '{name_or_desc}': {str(e)}")
        except Exception as e:
            logger.error(
                f"Unexpected error for '{name_or_desc}': {str(e)}", exc_info=True
            )

    if latest_values_data:
        fig, ax = plt.subplots(figsize=(12, 7))

        plot_names = [item[0][:40] for item in latest_values_data]
        plot_values = [item[1] for item in latest_values_data]

        ax.bar(plot_names, plot_values)
        ax.set_title("Latest Values for Different Variables/Series (v4.0)")
        ax.set_xlabel("Variable/Series")
        ax.set_ylabel("Value")
        plt.xticks(rotation=45, ha="right", fontsize=9)
        plt.tight_layout()
        save_plot(fig, "latest_values_v4.png")
    else:
        logger.warning("No data to plot for latest values.")


if __name__ == "__main__":
    main()
