import unittest
from unittest.mock import patch, Mock
from datetime import datetime, date
from bcra_connector import BCRAConnector, BCRAApiError, PrincipalesVariables, DatosVariable


class TestBCRAConnector(unittest.TestCase):
    """Test suite for the BCRAConnector class."""

    def setUp(self):
        """Set up a BCRAConnector instance for each test."""
        self.connector = BCRAConnector(verify_ssl=True)

    @patch('bcra_connector.requests.Session.get')
    def test_get_principales_variables(self, mock_get):
        """Test fetching principal variables."""
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
        self.assertEqual(result[0].idVariable, 1)
        self.assertEqual(result[0].descripcion, "Test Variable")
        self.assertEqual(result[0].fecha, date(2024, 3, 5))
        self.assertEqual(result[0].valor, 100.0)

    @patch('bcra_connector.requests.Session.get')
    def test_get_datos_variable(self, mock_get):
        """Test fetching data for a specific variable."""
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
        self.assertEqual(result[0].idVariable, 1)
        self.assertEqual(result[0].fecha, date(2024, 3, 5))
        self.assertEqual(result[0].valor, 100.0)

    def test_invalid_date_range(self):
        """Test handling of invalid date ranges."""
        with self.assertRaises(ValueError):
            self.connector.get_datos_variable(1, datetime(2024, 3, 5), datetime(2024, 3, 1))

    def test_date_range_too_long(self):
        """Test handling of date ranges exceeding one year."""
        with self.assertRaises(ValueError):
            self.connector.get_datos_variable(1, datetime(2024, 1, 1), datetime(2025, 1, 2))

    @patch('bcra_connector.requests.Session.get')
    def test_api_error(self, mock_get):
        """Test handling of API errors."""
        mock_get.side_effect = BCRAApiError("API Error")

        with self.assertRaises(BCRAApiError):
            self.connector.get_principales_variables()

    @patch('bcra_connector.BCRAConnector.get_principales_variables')
    def test_get_variable_history(self, mock_get_principales_variables):
        """Test fetching variable history for a non-existent variable."""
        mock_get_principales_variables.return_value = [
            PrincipalesVariables(idVariable=1, cdSerie=246, descripcion="Test Variable", fecha=date(2024, 3, 5),
                                 valor=100.0)
        ]
        with self.assertRaises(ValueError):
            self.connector.get_variable_history("Non-existent Variable")

    @patch('bcra_connector.BCRAConnector.get_datos_variable')
    def test_get_latest_value(self, mock_get_datos):
        """Test fetching the latest value for a variable."""
        mock_data = [
            DatosVariable(idVariable=1, fecha=date(2024, 3, 3), valor=95.0),
            DatosVariable(idVariable=1, fecha=date(2024, 3, 4), valor=97.5),
            DatosVariable(idVariable=1, fecha=date(2024, 3, 5), valor=100.0)
        ]
        mock_get_datos.return_value = mock_data

        result = self.connector.get_latest_value(1)

        self.assertIsInstance(result, DatosVariable)
        self.assertEqual(result.idVariable, 1)
        self.assertEqual(result.fecha, date(2024, 3, 5))
        self.assertEqual(result.valor, 100.0)

    def test_get_variable_by_name(self):
        """Test fetching a variable by its name."""
        with patch.object(self.connector, 'get_principales_variables') as mock_get:
            mock_get.return_value = [
                PrincipalesVariables(idVariable=1, cdSerie=246, descripcion="Test Variable", fecha=date(2024, 3, 5),
                                     valor=100.0)
            ]
            result = self.connector.get_variable_by_name("Test Variable")
            self.assertIsInstance(result, PrincipalesVariables)
            self.assertEqual(result.idVariable, 1)

    def test_get_variable_by_name_not_found(self):
        """Test handling of non-existent variable names."""
        with patch.object(self.connector, 'get_principales_variables') as mock_get:
            mock_get.return_value = [
                PrincipalesVariables(idVariable=1, cdSerie=246, descripcion="Test Variable", fecha=date(2024, 3, 5),
                                     valor=100.0)
            ]
            result = self.connector.get_variable_by_name("Non-existent Variable")
            self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
