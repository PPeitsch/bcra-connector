"""Unit tests for the BCRA Principal Variables models."""

import unittest
from datetime import date

from bcra_connector.principales_variables import DatosVariable, PrincipalesVariables


class TestPrincipalesVariables(unittest.TestCase):
    def test_principales_variables_from_dict(self):
        data = {
            "idVariable": 1,
            "cdSerie": 246,
            "descripcion": "Test Variable",
            "fecha": "2024-03-05",
            "valor": 100.0,
        }
        variable = PrincipalesVariables.from_dict(data)
        self.assertEqual(variable.idVariable, 1)
        self.assertEqual(variable.cdSerie, 246)
        self.assertEqual(variable.descripcion, "Test Variable")
        self.assertEqual(variable.fecha, date(2024, 3, 5))
        self.assertEqual(variable.valor, 100.0)

    def test_principales_variables_to_dict(self):
        variable = PrincipalesVariables(
            idVariable=1,
            cdSerie=246,
            descripcion="Test Variable",
            fecha=date(2024, 3, 5),
            valor=100.0,
        )
        data = variable.to_dict()
        self.assertEqual(data["idVariable"], 1)
        self.assertEqual(data["cdSerie"], 246)
        self.assertEqual(data["descripcion"], "Test Variable")
        self.assertEqual(data["fecha"], "2024-03-05")
        self.assertEqual(data["valor"], 100.0)

    def test_datos_variable_from_dict(self):
        data = {"idVariable": 1, "fecha": "2024-03-05", "valor": 100.0}
        dato = DatosVariable.from_dict(data)
        self.assertEqual(dato.idVariable, 1)
        self.assertEqual(dato.fecha, date(2024, 3, 5))
        self.assertEqual(dato.valor, 100.0)

    def test_datos_variable_to_dict(self):
        dato = DatosVariable(idVariable=1, fecha=date(2024, 3, 5), valor=100.0)
        data = dato.to_dict()
        self.assertEqual(data["idVariable"], 1)
        self.assertEqual(data["fecha"], "2024-03-05")
        self.assertEqual(data["valor"], 100.0)


if __name__ == "__main__":
    unittest.main()
