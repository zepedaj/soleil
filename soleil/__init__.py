
from . import base_functions, numpy_functions  # noqa - Registers the base functions.
from .utils import register, namespace  # noqa
from . import modifiers, functions  # noqa: Register base modifiers and functions


# __all__ = ['register', 'namespace']

"""
Motivation
==========

* Greater flexibility
  * Can represent any argument structure - the root does not need to be a dictionary.
  * Can add types that can also be represented and used for type-checking.
* Hidden nodes containing meta data
* Simpler code base
* Common type-checking interface
* Python-based syntax for interpolations, transparent to the user.
* Consistent, flexible conventions, easy to remember.
* Plays nicely with ``argparse`` -- can be used to define a parser parameter, or to auto-build a parser.
* Non-intrusive - does not auto-configure logging, does not require a rigid configuration file structure or output file name location.
* Meaningful error messages clearly indicating the node with problems.



Node system
============
* Node resolution
* $ strings
* Container nodes (lists, dictionaries)

Key nodes
==============

Reference strings
======================

Qualified names
===================
Qualified names are a special case of reference strings.

$-strings
============

"""
