from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bcra-connector",
    version="0.2.0",
    author="Pablo Peitsch",
    author_email="pablo.peitsch@gmail.com",
    description="A Python connector for the BCRA Estadísticas API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PPeitsch/bcra-connector",
    packages=find_packages(exclude=["tests", "docs"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.32.0,<2.33.0",
        "urllib3>=2.2.1,<3.0.0",
    ],
    extras_require={
        "dev": [
            "matplotlib>=3.7.3,<3.8.0",
            "setuptools>=70.0.0,<71.0.0",
            "pytest>=6.0.0,<8.0.0",
            "sphinx>=4.0.0,<6.0.0",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/PPeitsch/bcra-connector/issues",
        "Source": "https://github.com/PPeitsch/bcra-connector",
        "Documentation": "https://bcra-connector.readthedocs.io/bcra-connector/",
    },
)
