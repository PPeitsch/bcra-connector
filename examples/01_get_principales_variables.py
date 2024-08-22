from bcra_connector import BCRAConnector, BCRAApiError
import matplotlib.pyplot as plt


def main():
    # First, try with SSL verification
    connector = BCRAConnector()

    try:
        print("Fetching principal variables...")
        variables = connector.get_principales_variables()
    except BCRAApiError as e:
        print(f"Error occurred with SSL verification: {str(e)}")
        print("Retrying without SSL verification...")
        connector = BCRAConnector(verify_ssl=False)
        try:
            variables = connector.get_principales_variables()
        except BCRAApiError as e:
            print(f"Error occurred even without SSL verification: {str(e)}")
            return

    print(f"Found {len(variables)} variables.")
    print("\nFirst 5 variables:")
    for var in variables[:5]:
        print(f"ID: {var.id_variable}, Description: {var.descripcion}")
        print(f"  Latest value: {var.valor} ({var.fecha})")
        print()

    # Plot the first 10 variables
    plt.figure(figsize=(12, 6))
    plt.bar([var.descripcion[:20] for var in variables[:10]], [var.valor for var in variables[:10]])
    plt.title("Top 10 Principal Variables")
    plt.xlabel("Variables")
    plt.ylabel("Value")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig("principal_variables.png")
    print("Plot saved as 'principal_variables.png'")


if __name__ == "__main__":
    main()
