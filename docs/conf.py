import pathlib

import tomllib

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Carbon.txt Validator"
copyright = "2024, Chris Adams, Fershad Irani, Hannah Smith"
author = "Chris Adams, Fershad Irani, Hannah Smith"

pypproject_toml = pathlib.Path(".").absolute().parent / "pyproject.toml"
parsed_toml = tomllib.loads(pypproject_toml.read_text())

release = parsed_toml["project"]["version"]

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["myst_parser"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
