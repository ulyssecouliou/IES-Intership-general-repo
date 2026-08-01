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
if html_theme == "sphinx_rtd_theme":
    html_theme_options = {
        "collapse_navigation": False,
        "navigation_depth": 4,
        "sticky_navigation": True,
    }
else:
    html_theme_options = {
        "description": "IESVE Swiss SIA 380/2 and SIA 4010 readiness toolkit",
        "fixed_sidebar": True,
        "page_width": "1180px",
        "sidebar_width": "280px",
    }

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "private-members": True,
    "special-members": "__init__",
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_mock_imports = ["iesve"]
add_module_names = False
autosummary_generate = True
autodoc_class_signature = "mixed"
autodoc_typehints = "description"
autodoc_typehints_format = "short"
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
