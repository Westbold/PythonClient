#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="textverified",
    version="a0.0.x",
    url="https://github.com/pyasi/textverified",
    download_url="https://github.com/pyasi/textverified/archive/master.zip",
    author="Westbold LLC",
    packages=["textverified"],
    description="Python wrapper for the Textverified API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=["Textverified", "Verification", "Web Scraping", "API", "webhook", "python"],
    install_requires=["requests"],
)
