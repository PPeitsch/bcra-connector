"""Utility functions for generating test data."""

from datetime import date
from typing import Any, Dict, Optional


def create_test_variable(
    id_variable: int = 1, valor: float = 100.0, fecha: Optional[date] = None
) -> Dict[str, Any]:
    """Creates test data for variables.

    Args:
        id_variable: Variable ID
        valor: Variable value
        fecha: Date for the variable, defaults to today

    Returns:
        Dictionary with test variable data
    """
    if fecha is None:
        fecha = date.today()

    return {
        "idVariable": id_variable,
        "cdSerie": 246,
        "descripcion": f"Test Variable {id_variable}",
        "fecha": fecha.isoformat(),
        "valor": valor,
    }
