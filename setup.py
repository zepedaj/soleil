# !/usr/bin/env python

from setuptools import setup,  find_packages
setup(
    name='soleil',
    packages=find_packages('.', exclude=['tests']),
    version='0.1.0',
    description='',
    scripts=['soleil/solconf/bin/solex'],
    install_requires=['numpy', 'xerializer'],
    author='Joaquin Zepeda',
)
