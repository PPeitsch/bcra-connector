# Installation Guide

Getting started with BCRA API Connector is quick and easy. Follow these steps to install the library and begin accessing Argentina's economic data.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)

## Quick Installation

For most users, installing via pip is the simplest method:

```bash
pip install bcra-api-connector
```

This command will install the BCRA API Connector and all its dependencies.

## Installation for Development

If you're planning to contribute to the BCRA API Connector or need the latest development version, you can install directly from the GitHub repository:

```bash
pip install git+https://github.com/yourusername/bcra-api-connector.git
```

## Manual Installation

For those who prefer manual installation or are working in environments without internet access:

1. Download the source code from the [GitHub repository](https://github.com/yourusername/bcra-api-connector).
2. Navigate to the downloaded directory.
3. Run the following command:

```bash
python setup.py install
```

## Verifying the Installation

After installation, you can verify that BCRA API Connector is correctly installed by running:

```python
import bcra_connector
print(bcra_connector.__version__)
```

This should print the version number of the installed BCRA API Connector.

## Next Steps

Now that you have BCRA API Connector installed, you're ready to start fetching economic data! Head over to the [Usage Guide](usage.rst) to learn how to use the library.

If you encounter any issues during installation, please check our [Troubleshooting Guide](troubleshooting.rst) or open an issue on our [GitHub repository](https://github.com/yourusername/bcra-api-connector/issues).
