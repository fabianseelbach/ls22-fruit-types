# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'LS22 Best Fruit Types Calculator'
copyright = '2024, Fabian Seelbach'
author = 'Fabian Seelbach'

version = '0.0.1'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'sphinx_toolbox.more_autodoc',
    'sphinx.ext.autodoc'
]

templates_path = ['_templates']
exclude_patterns = []

language = 'de'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
