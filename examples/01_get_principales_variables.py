"""
Example demonstrating how to fetch and analyze principal variables from BCRA (Monetarias v3.0).
Shows basic usage, error handling, and data visualization.
"""

import logging
import os
import sys
from typing import Optional

import matplotlib.pyplot as plt

# Add the parent directory to the Python path to run examples directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.bcra_connector import BCRAApiError, BCRAConnector

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
    """Main function to demonstrate fetching principal variables."""
    connector = BCRAConnector(verify_ssl=False)

    try:
        logger.info("Fetching principal variables/monetary series (v3.0)...")
        variables = connector.get_principales_variables()
        logger.info(f"Found {len(variables)} variables/series.")

        if not variables:
            logger.warning("No variables returned from the API.")
            return

        logger.info("First 5 variables/series:")
        for var in variables[:5]:
            logger.info(
                f"ID: {var.idVariable}, Description: {var.descripcion}, "
                f"Category: {var.categoria}"
            )
            logger.info(f"  Latest value: {var.valor} ({var.fecha.isoformat()})")

        plot_count = min(10, len(variables))
        if plot_count > 0:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.bar(
                [
                    var.descripcion[:30] + f" ({var.categoria[:10]})"
                    for var in variables[:plot_count]
                ],
                [var.valor for var in variables[:plot_count]],
            )
            ax.set_title(f"Top {plot_count} Principal Variables/Series (v3.0)")
            ax.set_xlabel("Variables/Series (Category)")
            ax.set_ylabel("Value")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            save_plot(fig, "principal_variables_v3.png")
        else:
            logger.info("No variables to plot.")

        variable_name_to_search: Optional[str] = "Reservas Internacionales del BCRA"

        if not (
            variable_name_to_search
            and any(
                variable_name_to_search.lower() in v.descripcion.lower()
                for v in variables
                if v.descripcion
            )
        ):
            if variables:
                first_var_desc = getattr(variables[0], "descripcion", None)
                if first_var_desc:
                    variable_name_to_search = first_var_desc
                    logger.warning(
                        f"'Reservas Internacionales del BCRA' not found or initial search term was None, "
                        f"using first variable: '{variable_name_to_search}' for history example."
                    )
                else:
                    variable_name_to_search = None
            else:
                variable_name_to_search = None

        if variable_name_to_search:
            try:
                logger.info(f"Fetching history for: '{variable_name_to_search}'")
                history = connector.get_variable_history(
                    variable_name_to_search, days=30, limit=15
                )
                logger.info(
                    f"Historical data for '{variable_name_to_search}' (last 30 days, limit 15):"
                )
                if history:
                    for data_point in history[-5:]:
                        logger.info(
                            f"  {data_point.fecha.isoformat()}: {data_point.valor}"
                        )
                else:
                    logger.info(
                        f"No historical data returned for '{variable_name_to_search}'."
                    )
            except ValueError as e:
                logger.error(
                    f"Error fetching variable history for '{variable_name_to_search}': {str(e)}"
                )
        else:
            logger.info(
                "Skipping variable history example as no variable name was determined."
            )

    except BCRAApiError as e:
        logger.error(f"API Error occurred: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
