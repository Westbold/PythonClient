#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools
from pathlib import Path

try:
    import tomli as tomllib
except ImportError:
    import tomllib

# Load project metadata from pyproject.toml
pyproject_path = Path(__file__).parent / "pyproject.toml"
with open(pyproject_path, "rb") as f:
    pyproject_data = tomllib.load(f)

project = pyproject_data["project"]

# Load readme for description in PyPI
readme_path = Path(__file__).parent / "README.md"
with open(readme_path, "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name=project["name"],
    version=project["version"],
    url=project["urls"]["Homepage"],
    download_url=project["urls"]["Download"],
    author=project["authors"][0]["name"],
    packages=["textverified"],
    description=project["description"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    keywords=project["keywords"],
    install_requires=project["dependencies"],
    project_urls=project["urls"],
)
