# !/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="soleil_examples",
    # Use `./soleil_examples/setup.py` to install the soleil examples
    packages=find_packages(".", exclude=["solconf"]),
    version="0.1.0",
    description="",
    scripts=[],
    install_requires=["pglib", "soleil"],
    author="Joaquin Zepeda",
)
