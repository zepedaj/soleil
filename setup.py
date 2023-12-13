# !/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="soleil",
    # Use `./soleil_examples/setup.py` to install the soleil examples
    packages=find_packages(".", exclude=["tests", "data_for_tests", "soleil_examples"]),
    version="0.1.0",
    description="Soleil: Lucid Configurations",
    scripts=["scripts/solex"],
    install_requires=["jztools"],
    author="Joaquin Zepeda",
)
