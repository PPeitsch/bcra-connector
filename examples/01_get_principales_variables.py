from bcra_connector import BCRAConnector


def main():
    connector = BCRAConnector()

    print("Fetching principal variables...")
    variables = connector.get_principales_variables()

    print(f"Found {len(variables)} variables.")
    print("\nFirst 5 variables:")
    for var in variables[:5]:
        print(f"ID: {var.id_variable}, Description: {var.descripcion}")
        print(f"  Latest value: {var.valor} ({var.fecha})")
        print()


if __name__ == "__main__":
    main()
