import unittest
from datetime import date
from bcra_connector.cheques import (
    Entidad, ChequeDetalle, Cheque, EntidadResponse, ChequeResponse, ErrorResponse
)


class TestCheques(unittest.TestCase):

    def test_entidad(self):
        data = {
            "codigoEntidad": 11,
            "denominacion": "BANCO DE LA NACION ARGENTINA"
        }
        entidad = Entidad.from_dict(data)
        self.assertEqual(entidad.codigo_entidad, 11)
        self.assertEqual(entidad.denominacion, "BANCO DE LA NACION ARGENTINA")

    def test_cheque_detalle(self):
        data = {
            "sucursal": 524,
            "numeroCuenta": 5240055962,
            "causal": "Denunciado por tercero"
        }
        detalle = ChequeDetalle.from_dict(data)
        self.assertEqual(detalle.sucursal, 524)
        self.assertEqual(detalle.numero_cuenta, 5240055962)
        self.assertEqual(detalle.causal, "Denunciado por tercero")

    def test_cheque(self):
        data = {
            "numeroCheque": 20377516,
            "denunciado": True,
            "fechaProcesamiento": "2024-05-24",
            "denominacionEntidad": "BANCO DE LA NACION ARGENTINA",
            "detalles": [
                {
                    "sucursal": 524,
                    "numeroCuenta": 5240055962,
                    "causal": "Denunciado por tercero"
                }
            ]
        }
        cheque = Cheque.from_dict(data)
        self.assertEqual(cheque.numero_cheque, 20377516)
        self.assertTrue(cheque.denunciado)
        self.assertEqual(cheque.fecha_procesamiento, date(2024, 5, 24))
        self.assertEqual(cheque.denominacion_entidad, "BANCO DE LA NACION ARGENTINA")
        self.assertEqual(len(cheque.detalles), 1)
        self.assertEqual(cheque.detalles[0].sucursal, 524)

    def test_cheque_to_dict(self):
        cheque = Cheque(
            numero_cheque=20377516,
            denunciado=True,
            fecha_procesamiento=date(2024, 5, 24),
            denominacion_entidad="BANCO DE LA NACION ARGENTINA",
            detalles=[ChequeDetalle(sucursal=524, numero_cuenta=5240055962, causal="Denunciado por tercero")]
        )
        cheque_dict = cheque.to_dict()
        self.assertEqual(cheque_dict['numeroCheque'], 20377516)
        self.assertTrue(cheque_dict['denunciado'])
        self.assertEqual(cheque_dict['fechaProcesamiento'], "2024-05-24")
        self.assertEqual(cheque_dict['denominacionEntidad'], "BANCO DE LA NACION ARGENTINA")
        self.assertEqual(len(cheque_dict['detalles']), 1)
        self.assertEqual(cheque_dict['detalles'][0]['sucursal'], 524)

    def test_entidad_response(self):
        data = {
            "status": 200,
            "results": [
                {
                    "codigoEntidad": 11,
                    "denominacion": "BANCO DE LA NACION ARGENTINA"
                },
                {
                    "codigoEntidad": 14,
                    "denominacion": "BANCO DE LA PROVINCIA DE BUENOS AIRES"
                }
            ]
        }
        response = EntidadResponse.from_dict(data)
        self.assertEqual(response.status, 200)
        self.assertEqual(len(response.results), 2)
        self.assertEqual(response.results[0].codigo_entidad, 11)
        self.assertEqual(response.results[1].denominacion, "BANCO DE LA PROVINCIA DE BUENOS AIRES")

    def test_cheque_response(self):
        data = {
            "status": 200,
            "results": {
                "numeroCheque": 20377516,
                "denunciado": True,
                "fechaProcesamiento": "2024-05-24",
                "denominacionEntidad": "BANCO DE LA NACION ARGENTINA",
                "detalles": [
                    {
                        "sucursal": 524,
                        "numeroCuenta": 5240055962,
                        "causal": "Denunciado por tercero"
                    }
                ]
            }
        }
        response = ChequeResponse.from_dict(data)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.results.numero_cheque, 20377516)
        self.assertTrue(response.results.denunciado)
        self.assertEqual(response.results.fecha_procesamiento, date(2024, 5, 24))
        self.assertEqual(len(response.results.detalles), 1)

    def test_error_response(self):
        data = {
            "status": 400,
            "errorMessages": ["Validar formato de los parámetros enviados."]
        }
        response = ErrorResponse.from_dict(data)
        self.assertEqual(response.status, 400)
        self.assertEqual(len(response.error_messages), 1)
        self.assertEqual(response.error_messages[0], "Validar formato de los parámetros enviados.")


if __name__ == '__main__':
    unittest.main()
