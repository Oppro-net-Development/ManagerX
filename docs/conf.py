# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath('../src'))
sys.setrecursionlimit(2500)

# -- Project information -----------------------------------------------------
project = 'ManagerX'
copyright = '2025, OPPRO.NET Network'
author = 'OPPRO.NET Development'
release = '2.0.0'
version = '2.0'       # Kurzversion
language = 'en'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.githubpages',
    'sphinx.ext.autosummary',
    'sphinx_autodoc_typehints',
    'myst_parser',
    'sphinx_copybutton',
]

autosummary_generate = True
todo_include_todos = True

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Intersphinx Mapping (für Cross-Referenzen)
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'requests': ('https://docs.python-requests.org/en/latest/', None),
}

# Markdown Einstellungen
myst_enable_extensions = [
    "colon_fence", 
    "deflist", 
    "html_admonition", 
    "html_image",
]

# -- Options for HTML output -------------------------------------------------
html_theme = 'pydata_sphinx_theme'
html_favicon = "_static/managerx.png"
html_static_path = ['_static']
html_css_files = [
    'custom.css',
]
html_theme_options = {
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/Oppro-net-Development/ManagerX",  # required
            "icon": "fa-brands fa-square-github",
            "type": "fontawesome",
        }
   ],
}