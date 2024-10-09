# BCRA API Connector

Un conector Python para las APIs del BCRA (Banco Central de la República Argentina), incluyendo Estadísticas v2.0, Cheques y Estadísticas Cambiarias.

## Características

- Obtener variables principales publicadas por el BCRA
- Recuperar datos históricos de variables específicas
- Obtener el último valor de una variable
- Acceder a información sobre cheques denunciados
- Obtener datos de tipos de cambio
- Soporte bilingüe (español e inglés)
- Manejo de errores con excepciones personalizadas
- Lógica de reintentos con retroceso exponencial
- Verificación SSL (opcional)
- Modo de depuración para registro detallado

## Instalación

```bash
pip install bcra-connector
```

## Requisitos

- Python 3.9 o superior
- requests>=2.32.0,<2.33
- matplotlib>=3.7.3,<3.8
- setuptools>=70.0.0,<71
- urllib3>=2.2.1,<3.0
- numpy~=1.26.4,<1.27
- scipy~=1.14.1,<1.15

## Inicio Rápido

```python
from bcra_connector import BCRAConnector
from datetime import datetime, timedelta

# Inicializar el conector
connector = BCRAConnector()

# Obtener todas las variables principales
variables = connector.get_principales_variables()
for var in variables[:5]:  # Imprimir las primeras 5 por brevedad
    print(f"{var.descripcion}: {var.valor} ({var.fecha})")

# Obtener datos de una variable específica (ej., Reservas Internacionales del BCRA)
id_variable = 1
fecha_fin = datetime.now()
fecha_inicio = fecha_fin - timedelta(days=30)
datos = connector.get_datos_variable(id_variable, fecha_inicio, fecha_fin)
for dato in datos[-5:]:  # Imprimir los últimos 5 por brevedad
    print(f"{dato.fecha}: {dato.valor}")

# Obtener el último valor de una variable
ultimo = connector.get_latest_value(id_variable)
print(f"Último valor para la Variable {id_variable}: {ultimo.valor} ({ultimo.fecha})")

# Obtener información sobre cheques denunciados
entidades = connector.get_entidades()
cheque = connector.get_cheque_denunciado(entidades[0].codigo_entidad, 12345678)
print(f"Estado del cheque: {'Denunciado' if cheque.denunciado else 'No denunciado'}")

# Obtener tipos de cambio
divisas = connector.get_divisas()
cotizaciones = connector.get_cotizaciones()
for detalle in cotizaciones.detalle[:5]:  # Imprimir las primeras 5 por brevedad
    print(f"{detalle.codigo_moneda}: {detalle.tipo_cotizacion}")
```

## Documentación

Para documentación detallada, incluyendo ejemplos de uso y referencia de la API, por favor visite nuestra [Documentación en Read The Docs](https://bcra-connector.readthedocs.io/).

## Contribuir

¡Las contribuciones son bienvenidas! Por favor, lea nuestras [Guías de Contribución](CONTRIBUTING.md) para obtener detalles sobre cómo enviar pull requests, reportar problemas y sugerir mejoras.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - vea el archivo [LICENSE](LICENSE) para más detalles.

## Registro de Cambios

Para una lista detallada de cambios y actualizaciones de versiones, por favor consulte el [Registro de Cambios](https://bcra-connector.readthedocs.io/en/latest/changelog.html).

## Descargo de Responsabilidad

Este proyecto no está oficialmente afiliado ni respaldado por el Banco Central de la República Argentina. Úselo bajo su propio riesgo.