import unittest
from datetime import date

from bcra_connector.estadisticas_cambiarias import (
    CotizacionDetalle,
    CotizacionesResponse,
    CotizacionFecha,
    CotizacionResponse,
    Divisa,
    DivisaResponse,
    ErrorResponse,
    Metadata,
    Resultset,
)


class TestEstadisticasCambiarias(unittest.TestCase):

    def test_divisa(self):
        data = {"codigo": "USD", "denominacion": "DOLAR ESTADOUNIDENSE"}
        divisa = Divisa.from_dict(data)
        self.assertEqual(divisa.codigo, "USD")
        self.assertEqual(divisa.denominacion, "DOLAR ESTADOUNIDENSE")

    def test_cotizacion_detalle(self):
        data = {
            "codigoMoneda": "USD",
            "descripcion": "DOLAR ESTADOUNIDENSE",
            "tipoPase": 1.0,
            "tipoCotizacion": 43.6862,
        }
        detalle = CotizacionDetalle.from_dict(data)
        self.assertEqual(detalle.codigo_moneda, "USD")
        self.assertEqual(detalle.descripcion, "DOLAR ESTADOUNIDENSE")
        self.assertEqual(detalle.tipo_pase, 1.0)
        self.assertEqual(detalle.tipo_cotizacion, 43.6862)

    def test_cotizacion_fecha(self):
        data = {
            "fecha": "2024-06-12",
            "detalle": [
                {
                    "codigoMoneda": "USD",
                    "descripcion": "DOLAR ESTADOUNIDENSE",
                    "tipoPase": 1.0,
                    "tipoCotizacion": 43.6862,
                }
            ],
        }
        cotizacion = CotizacionFecha.from_dict(data)
        self.assertEqual(cotizacion.fecha, date(2024, 6, 12))
        self.assertEqual(len(cotizacion.detalle), 1)
        self.assertEqual(cotizacion.detalle[0].codigo_moneda, "USD")

    def test_cotizacion_fecha_to_dict(self):
        cotizacion = CotizacionFecha(
            fecha=date(2024, 6, 12),
            detalle=[
                CotizacionDetalle(
                    codigo_moneda="USD",
                    descripcion="DOLAR ESTADOUNIDENSE",
                    tipo_pase=1.0,
                    tipo_cotizacion=43.6862,
                )
            ],
        )
        data = cotizacion.to_dict()
        self.assertEqual(data["fecha"], "2024-06-12")
        self.assertEqual(len(data["detalle"]), 1)
        self.assertEqual(data["detalle"][0]["codigoMoneda"], "USD")

    def test_resultset(self):
        data = {"count": 1, "offset": 0, "limit": 1000}
        resultset = Resultset.from_dict(data)
        self.assertEqual(resultset.count, 1)
        self.assertEqual(resultset.offset, 0)
        self.assertEqual(resultset.limit, 1000)

    def test_metadata(self):
        data = {"resultset": {"count": 1, "offset": 0, "limit": 1000}}
        metadata = Metadata.from_dict(data)
        self.assertEqual(metadata.resultset.count, 1)
        self.assertEqual(metadata.resultset.offset, 0)
        self.assertEqual(metadata.resultset.limit, 1000)

    def test_divisa_response(self):
        data = {
            "status": 200,
            "results": [
                {"codigo": "USD", "denominacion": "DOLAR ESTADOUNIDENSE"},
                {"codigo": "EUR", "denominacion": "EURO"},
            ],
        }
        response = DivisaResponse.from_dict(data)
        self.assertEqual(response.status, 200)
        self.assertEqual(len(response.results), 2)
        self.assertEqual(response.results[0].codigo, "USD")
        self.assertEqual(response.results[1].denominacion, "EURO")

    def test_cotizacion_response(self):
        data = {
            "status": 200,
            "results": {
                "fecha": "2024-06-12",
                "detalle": [
                    {
                        "codigoMoneda": "USD",
                        "descripcion": "DOLAR ESTADOUNIDENSE",
                        "tipoPase": 1.0,
                        "tipoCotizacion": 43.6862,
                    }
                ],
            },
        }
        response = CotizacionResponse.from_dict(data)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.results.fecha, date(2024, 6, 12))
        self.assertEqual(len(response.results.detalle), 1)
        self.assertEqual(response.results.detalle[0].codigo_moneda, "USD")

    def test_cotizaciones_response(self):
        data = {
            "status": 200,
            "metadata": {"resultset": {"count": 1, "offset": 0, "limit": 1000}},
            "results": [
                {
                    "fecha": "2024-06-12",
                    "detalle": [
                        {
                            "codigoMoneda": "USD",
                            "descripcion": "DOLAR ESTADOUNIDENSE",
                            "tipoPase": 1.0,
                            "tipoCotizacion": 43.6862,
                        }
                    ],
                }
            ],
        }
        response = CotizacionesResponse.from_dict(data)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.metadata.resultset.count, 1)
        self.assertEqual(len(response.results), 1)
        self.assertEqual(response.results[0].fecha, date(2024, 6, 12))
        self.assertEqual(response.results[0].detalle[0].codigo_moneda, "USD")

    def test_error_response(self):
        data = {
            "status": 400,
            "errorMessages": [
                "Parámetro erróneo: La fecha desde no puede ser mayor a la fecha hasta."
            ],
        }
        response = ErrorResponse.from_dict(data)
        self.assertEqual(response.status, 400)
        self.assertEqual(len(response.error_messages), 1)
        self.assertEqual(
            response.error_messages[0],
            "Parámetro erróneo: La fecha desde no puede ser mayor a la fecha hasta.",
        )

    def test_cotizacion_fecha_with_null_date(self):
        data = {"fecha": None, "detalle": []}
        cotizacion = CotizacionFecha.from_dict(data)
        self.assertIsNone(cotizacion.fecha)
        self.assertEqual(len(cotizacion.detalle), 0)


if __name__ == "__main__":
    unittest.main()
