# Installation Guide

This guide provides detailed instructions for installing the BCRA API Connector using various methods.

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

## Installation in a Virtual Environment

It's often recommended to install Python packages in a virtual environment to avoid conflicts with other projects or system-wide packages:

1. Create a virtual environment:
   ```bash
   python -m venv bcra_env
   ```

2. Activate the virtual environment:
   - On Windows:
     ```bash
     bcra_env\Scripts\activate
     ```
   - On macOS and Linux:
     ```bash
     source bcra_env/bin/activate
     ```

3. Install the BCRA API Connector:
   ```bash
   pip install bcra-api-connector
   ```

## Verifying the Installation

After installation, you can verify that BCRA API Connector is correctly installed by running:

```python
import bcra_connector
print(bcra_connector.__version__)
```

This should print the version number of the installed BCRA API Connector.

## Dependencies

The BCRA API Connector has the following dependencies:

- requests>=2.32.0,<2.33
- matplotlib>=3.7.3,<3.8
- setuptools>=70.0.0,<71
- urllib3>=2.2.1,<3.0

These will be automatically installed when using pip. If you're installing manually, ensure these dependencies are installed.

## Troubleshooting

If you encounter any issues during installation, please check our [Troubleshooting Guide](troubleshooting.rst) or open an issue on our [GitHub repository](https://github.com/yourusername/bcra-api-connector/issues).

## Next Steps

Now that you have BCRA API Connector installed, you're ready to start fetching economic data! Head over to the [Usage Guide](usage.rst) to learn how to use the library.