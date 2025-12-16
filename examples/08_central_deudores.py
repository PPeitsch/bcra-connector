#!/usr/bin/env python
"""
Example 5: Central de Deudores (Debtor Registry)

This example demonstrates how to query debtor information from BCRA's
Central de Deudores API, including current debts, historical debts,
and rejected checks.

Note: You need a valid CUIT/CUIL/CDI (11 digits) for these queries.
The API returns information about the debtor's credit status in the
Argentine financial system.
"""

from bcra_connector import BCRAApiError, BCRAConnector


def demonstrate_central_deudores() -> None:
    """Demonstrate Central de Deudores API usage."""
    # Initialize connector
    connector = BCRAConnector(debug=True)

    # Example CUIT (you should use a valid one for real queries)
    # Note: This is a demo CUIT that may return "not found"
    cuit = "20123456789"

    print("=" * 60)
    print("Central de Deudores API Demo")
    print("=" * 60)

    # 1. Query current debts
    print("\n1. Fetching current debts...")
    try:
        deudor = connector.get_deudas(cuit)
        print(f"   Identificación: {deudor.identificacion}")
        print(f"   Denominación: {deudor.denominacion}")
        print(f"   Periodos: {len(deudor.periodos)}")

        if deudor.periodos:
            latest_periodo = deudor.periodos[0]
            print(f"   Último periodo: {latest_periodo.periodo}")
            for entidad in latest_periodo.entidades:
                print(f"     - {entidad.entidad}: Sit. {entidad.situacion}, ${entidad.monto}k")

            # Convert to DataFrame (requires pandas)
            try:
                df = deudor.to_dataframe()
                print(f"\n   DataFrame shape: {df.shape}")
                print(df.head())
            except ImportError:
                print("   (Install pandas for DataFrame support)")

    except BCRAApiError as e:
        print(f"   Error: {e}")

    # 2. Query historical debts (24 months)
    print("\n2. Fetching historical debts (24 months)...")
    try:
        historico = connector.get_deudas_historicas(cuit)
        print(f"   Total periods in history: {len(historico.periodos)}")

        if historico.periodos:
            print("   First 5 periods:")
            for periodo in historico.periodos[:5]:
                total_entidades = len(periodo.entidades)
                total_deuda = sum(e.monto for e in periodo.entidades)
                print(f"     - {periodo.periodo}: {total_entidades} entities, ${total_deuda}k total")

    except BCRAApiError as e:
        print(f"   Error: {e}")

    # 3. Query rejected checks
    print("\n3. Fetching rejected checks...")
    try:
        cheques = connector.get_cheques_rechazados(cuit)
        print(f"   Identificación: {cheques.identificacion}")
        print(f"   Denominación: {cheques.denominacion}")
        print(f"   Causales: {len(cheques.causales)}")

        for causal in cheques.causales:
            total_cheques = sum(len(e.detalle) for e in causal.entidades)
            print(f"     - {causal.causal}: {total_cheques} checks")

            # Show first check detail
            if causal.entidades and causal.entidades[0].detalle:
                cheque = causal.entidades[0].detalle[0]
                print(f"       Example: Check #{cheque.nro_cheque}, ${cheque.monto}")

        # Convert to DataFrame
        try:
            df = cheques.to_dataframe()
            print(f"\n   Rejected checks DataFrame shape: {df.shape}")
        except ImportError:
            print("   (Install pandas for DataFrame support)")

    except BCRAApiError as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_central_deudores()
