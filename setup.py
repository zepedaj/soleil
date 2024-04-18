# !/usr/bin/env python

from setuptools import setup, find_packages

test_requires = ["freezegun"]

with open("README.md") as f:
    long_description = f.read()

setup(
    name="soleil",
    # Use `./soleil_examples/setup.py` to install the soleil examples
    packages=find_packages(".", exclude=["tests", "data_for_tests", "soleil_examples"]),
    version="0.1.0",
    scripts=["scripts/solex"],
    install_requires=["jztools", "climax", "rich"] + test_requires,
    author="Joaquin Zepeda",
    description="Soleil: Lucid Configurations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zepedaj/soleil",
)
