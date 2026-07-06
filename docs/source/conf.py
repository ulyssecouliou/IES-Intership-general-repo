"""Sphinx configuration for the Swiss SIA Compliance Checker."""

from __future__ import annotations

import os
import sys
import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

project = "Swiss SIA Compliance Checker"
author = "IESVE Swiss Compliance Team"
copyright = "2026, IESVE Swiss Compliance Team"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

if importlib.util.find_spec("myst_parser") is not None:
    extensions.append("myst_parser")

templates_path = ["_templates"]
exclude_patterns = []

language = os.getenv("SPHINX_LANGUAGE", "en")
locale_dirs = ["locales/"]
gettext_compact = False

html_theme = (
    "sphinx_rtd_theme"
    if importlib.util.find_spec("sphinx_rtd_theme") is not None
    else "alabaster"
)
html_title = "Swiss SIA Compliance Checker"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "private-members": True,
    "special-members": "__init__",
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_mock_imports = ["iesve"]
autosummary_generate = True
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
