from datetime import date


def create_test_variable(id_variable=1, valor=100.0, fecha=None):
    """Creates test data for variables.

    Args:
        id_variable (int): Variable ID
        valor (float): Variable value
        fecha (date, optional): Date for the variable. Defaults to today.

    Returns:
        dict: Dictionary with test variable data
    """
    if fecha is None:
        fecha = date.today()
    return {
        "idVariable": id_variable,
        "cdSerie": 246,
        "descripcion": f"Test Variable {id_variable}",
        "fecha": fecha.isoformat(),
        "valor": valor
    }
