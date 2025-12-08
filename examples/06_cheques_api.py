"""
Example demonstrating the Checks (Cheques) API module.
Shows how to fetch financial entities and check reported checks.
"""

import logging

from bcra_connector import BCRAApiError, BCRAConnector

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main function to demonstrate Checks API usage."""
    connector = BCRAConnector(verify_ssl=False)

    try:
        # 1. List Entities
        logger.info("Fetching financial entities...")
        entities = connector.get_entidades()
        logger.info(f"Found {len(entities)} entities.")

        if not entities:
            logger.warning("No entities found.")
            return

        logger.info("First 5 entities:")
        for entity in entities[:5]:
            logger.info(f"  Code: {entity.codigo_entidad}, Name: {entity.denominacion}")

        # 2. Check a specific check (Simulated)
        # We'll use the first entity found
        target_entity = entities[0]
        check_number = 123456  # Dummy check number

        logger.info(
            f"Checking check status {check_number} for {target_entity.denominacion} (Code: {target_entity.codigo_entidad})..."
        )

        # Method A: check_denunciado helper (returns boolean)
        try:
            is_denounced = connector.check_denunciado(
                target_entity.denominacion, check_number
            )
            logger.info(
                f"Check {check_number} denounced status (via check_denunciado): {is_denounced}"
            )
        except Exception as e:
            logger.warning(f"Helper check_denunciado failed: {e}")

        # Method B: get_cheque_denunciado (returns Cheque object or raises error)
        try:
            cheque_info = connector.get_cheque_denunciado(
                target_entity.codigo_entidad, check_number
            )
            logger.info(f"Cheque info found: {cheque_info}")
        except BCRAApiError as e:
            # It is expected to fail with 404 if the check is not denounced/found
            logger.info(
                f"get_cheque_denunciado result: {e} (This usually means the check is not denounced)"
            )

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
