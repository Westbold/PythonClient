# Configuration file for the Sphinx documentation builder.

import os
import sys
from pathlib import Path

try:
    import tomli as tomllib
except ImportError:
    import tomllib

# -- Path setup --------------------------------------------------------------
sys.path.insert(0, os.path.abspath(".."))

# Load project metadata from pyproject.toml
pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
with open(pyproject_path, "rb") as f:
    pyproject_data = tomllib.load(f)

project_data = pyproject_data["project"]

# -- Project information -----------------------------------------------------
project = "TextVerified Python Client"
copyright = "2025, " + project_data["authors"][0]["name"]
author = project_data["authors"][0]["name"]
release = project_data["version"]

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

# Theme options for cleaner look
html_theme_options = {
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 3,
    "includehidden": True,
    "titles_only": False,
}

# -- Extension configuration -------------------------------------------------
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "exclude-members": "__weakref__",
    "undoc-members": True,
}

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True

# Autodoc settings for clean output
autodoc_typehints = "signature"
autodoc_member_order = "bysource"
add_module_names = False


# Custom autodoc processing
def skip_redundant_members(app, what, name, obj, skip, options):
    """Skip redundant documentation but keep enum values."""

    # Always show enum values
    try:
        from enum import Enum

        if what == "attribute" and isinstance(obj, Enum):
            return False
    except (ImportError, AttributeError):
        pass

    # Skip dataclass internals
    if name in ["__dataclass_fields__", "__dataclass_params__", "__match_args__", "__weakref__"]:
        return True

    # Skip redundant methods
    if what == "method" and name in ["__eq__", "__repr__", "__hash__", "__init__", "to_api", "from_api"]:
        return True

    return skip


def setup(app):
    app.connect("autodoc-skip-member", skip_redundant_members)
