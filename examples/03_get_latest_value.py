from bcra_connector import BCRAConnector, BCRAApiError


def main():
    connector = BCRAConnector()

    # Let's get the latest value for a few different variables
    variable_ids = [1, 4, 5]  # Example variable IDs

    for id_variable in variable_ids:
        try:
            print(f"Fetching latest value for variable ID {id_variable}...")
            latest = connector.get_latest_value(id_variable)
            print(f"Latest value: {latest.valor} ({latest.fecha})")
            print()
        except BCRAApiError as e:
            print(f"An error occurred for variable ID {id_variable}: {str(e)}")
            print()


if __name__ == "__main__":
    main()
