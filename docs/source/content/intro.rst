Motivation
==========


* [TODO] Leverages the :mod:`xerializer` package to support custom type type-checking and config file or CLI object representation.

* Near-no-code CLI experiment launching.

* Leverages Python's built-in `Abstract Syntax Tree <https://docs.python.org/3/library/ast.html>`_ support.

  * Simple, rich, Python-based syntax for configuration value resolution.
  * Restricted for safety, user-extensible.

* Flexible configuration node tree system

  * Supports hidden nodes that are visible to other nodes when rendering, but not included in the final rendered configuration.
  * Can represent any argument structure - the root does not need to be a dictionary.

* [TODO] Plays nicely with `argparse <https://docs.python.org/3/library/argparse.html>`_ -- can be used to define an argparse parameter, or to auto-build a CLI from a config file.

* Simple, well-documented code base.
* Common type-checking interface
* Consistent, flexible conventions, easy to remember.
* Non-intrusive 

  * Does not auto-configure logging or output file location. 
  * Does not require a rigid configuration file structure or output file name location.

* Meaningful error messages clearly indicating configuration nodes with problems.

  * Configuration values cyclical dependencies detected automatically and signaled to the user.
  * [TODO] Config source file causing the error included in error message.


Installation
============

.. code-block:: bash

  pip install soleil

Getting started
===============


Basic :class:`SolConf` objects
-------------------------------

Basic :class:`SolConf` objects can be built from compositions of serializable types (i.e., those types that can be represented natively in **JSON** or **YAML** format):

   * ``int``, ``float``, ``str``, ``list`` and
   * ``dict`` (with string keys that are valid variable names).

.. testcode:: SolConf

   from soleil import SolConf

   sc = SolConf(1.0)

Calling a :class:`SolConf` object returns its **resolve** value. For simple input, the resolved value is the same as the original input:

.. testcode:: SolConf

   # Base types
   for raw in [1, 2.0, 'abc', [1,2,'abc']]:
     sc = SolConf(raw)
     assert sc() == raw
     
   # Dictionaries - keys must be valid variable names.
   for raw in [{'var0':0, 'var1':1, 'var2':2}]:
      sc = SolConf(raw)
      assert sc() == raw


Compositions of these base types are also valid input:

.. testcode:: SolConf

  # Base type compositions are valid too.
  raw_data = {
    'var0': [0, 1, 2, 'abc', {'var1':[3,4,'xyz']}],
    'var2': 5
  }
  assert SolConf(raw_data)() == raw_data    
     
$-strings
============

The power of :class:`SolConf` objects comes from its ability to interpret **$-strings** -- special strings indicated by a ``'$:'`` prefix such as

.. testcode::

  SolConf('$:1+2')




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

