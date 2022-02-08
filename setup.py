# !/usr/bin/env python

from setuptools import setup,  find_packages
setup(
    name='soleil',
    packages=find_packages('.', exclude=['tests']),
    version='0.1.0',
    description='',
    install_requires=['numpy', 'xerializer'],
    author='Joaquin Zepeda',
)
