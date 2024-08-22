import unittest
from unittest.mock import patch, Mock
from datetime import datetime
from bcra_connector import BCRAConnector, BCRAApiError, PrincipalesVariables, DatosVariable


class TestBCRAConnector(unittest.TestCase):

    def setUp(self):
        self.connector = BCRAConnector()

    @patch('bcra_connector.requests.Session.get')
    def test_get_principales_variables(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "idVariable": 1,
                    "cdSerie": 246,
                    "descripcion": "Test Variable",
                    "fecha": "2024-03-05",
                    "valor": 100.0
                }
            ]
        }
        mock_get.return_value = mock_response

        result = self.connector.get_principales_variables()

        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], PrincipalesVariables)
        self.assertEqual(result[0].id_variable, 1)
        self.assertEqual(result[0].descripcion, "Test Variable")

    @patch('bcra_connector.requests.Session.get')
    def test_get_datos_variable(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "idVariable": 1,
                    "fecha": "2024-03-05",
                    "valor": 100.0
                }
            ]
        }
        mock_get.return_value = mock_response

        result = self.connector.get_datos_variable(1, datetime(2024, 3, 1), datetime(2024, 3, 5))

        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], DatosVariable)
        self.assertEqual(result[0].id_variable, 1)
        self.assertEqual(result[0].fecha, "2024-03-05")

    def test_invalid_date_range(self):
        with self.assertRaises(ValueError):
            self.connector.get_datos_variable(1, datetime(2024, 3, 5), datetime(2024, 3, 1))

    def test_date_range_too_long(self):
        with self.assertRaises(ValueError):
            self.connector.get_datos_variable(1, datetime(2024, 1, 1), datetime(2025, 1, 2))

    @patch('bcra_connector.requests.Session.get')
    def test_api_error(self, mock_get):
        mock_get.side_effect = BCRAApiError("API Error")

        with self.assertRaises(BCRAApiError):
            self.connector.get_principales_variables()


if __name__ == '__main__':
    unittest.main()
