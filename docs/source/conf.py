import os
import sys

# Add the parent directory to the Python path to allow importing bcra_connector
sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------
project = 'BCRA API Connector'
copyright = '2024, Pablo Peitsch'
author = 'Pablo Peitsch'

# The full version, including alpha/beta/rc tags
release = '0.2.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'

# Correct the static path
html_static_path = ['../build/_static']

# -- Extension configuration -------------------------------------------------
autodoc_member_order = 'bysource'
napoleon_google_docstring = False
napoleon_use_param = False
napoleon_use_ivar = True

# Add the examples directory to the list of extra paths
html_extra_path = ['../../examples']
