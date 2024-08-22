from bcra_connector import BCRAConnector, BCRAApiError


def main():
    # Default usage (production-like)
    connector_prod = BCRAConnector()
    print("Production-like connector:")
    try:
        variables = connector_prod.get_principales_variables()
        print(f"Found {len(variables)} variables.")
    except BCRAApiError as e:
        print(f"API Error: {str(e)}")

    print("\n" + "=" * 50 + "\n")

    # Development/testing usage (SSL verification disabled, debug on)
    connector_dev = BCRAConnector(verify_ssl=False, debug=True)
    print("Development connector (SSL verification disabled, debug on):")
    try:
        variables = connector_dev.get_principales_variables()
        print(f"Found {len(variables)} variables.")
    except BCRAApiError as e:
        print(f"API Error: {str(e)}")


if __name__ == "__main__":
    main()
