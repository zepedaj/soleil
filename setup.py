# !/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="soleil",
    packages=find_packages(".", exclude=["tests", "data_for_tests"]),
    version="0.1.0",
    description="",
    scripts=["scripts/solex"],
    # install_requires=["numpy", "xerializer"],
    install_requires=["pglib"],
    author="Joaquin Zepeda",
)
