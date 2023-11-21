Introduction
################

Soleil is a Python object configuration mechanism inspired by Facebook's Hydra that enjoys the following benefits:

* Soleil configuration files (``*.solconf`` files) use familiar Python syntax and can describe any installed function call, Python object, or composition thereof.
* Soleil configuration files can be organized into portable, Python-like packages with one or more root configurations. Packages can further be used within other packages. Any file whithin a package can be a root configuration that is loaded with ``load_config()`` and implicitly defines a package consisting of all solconf files in the same directory and all sub-directories.
* Soleil includes the built-in command line tool :mod:`solex` that automatically converts any soleil package into a fully fledged, extensible command line utility that plays nicely with the builtin
   :mod:`argparse` module.
        * Soleil configuration packages can also be added directly to :mod:`argparse` parsers as arguments that resolve to the object described by the loaded configuration.
* CLI tools that take soleil configured objects as arguments inherit the ability to override any component of the package from the command line using a subset of Python syntax.


Soleil Pre-processor
=======================

Various functionalities provided by soleil rely on Python language modifications carried out by the **soleil pre-processor**. The pre-processor exploits Python's :ref:`ast module` to modify the parsed syntax tree extracted from each solconf file. While these code modifications should be transparent to the user, it is useful to know what they are.



Pre-processor Directives
=========================

 :func:`load`
---------------

When used as a simple assignment such as


.. code-block::

    a = load('.option')


the pre-processor will automatically inject the target name keyword argument to load as follows:

.. code-block::

    a = load('.option', _target='a')




:func:`promoted`
-----------------

See the documentation for :func:`promoted`. Promoted members are skipped when building :ref:`variable name paths` and thus the name of the promoted module member needs to be known before the module executes. Extracting this name is part of the job the pre-processor does.


Converting assignments to override checks
-------------------------------------------

The pre-processor converts any variable assignment to a call to the soleil override checker:

For example, the code

.. code-block::

   a = 1

is converted to

.. code-block::

   a = _soleil_override('a', 1)

The :func:`_soleil_override` function is not a user-facing function but rather operates under the hood. Its main task is to check the provided CLI overrides and return the matching one, if any, or the original value otherwise.

Hiding imported members
------------------------

The pre-processor also checks whether any imports are done within a solconf module and adds those names to the list of default-hidden module members that will not be passed as keywords to the module's type call.

Overriding Configurations
===========================


Syntax
------------

The :func:`~soleil.load_config` function supports specifying values that will override those in the loaded configuration by means of its ``overrides`` parameter which must be a list with entries of various possible types (see :class:`OverrideSpec`):

.. testcode::

   from soleil import load_config

   obj = load_config('./main.solconf', overrides=[...])


For example, entries of ``overrides`` can be strings in various python-syntax-compatible forms, possibly specifying more than one override in each entry:

.. testcode::

   overrides=['a=3']
   overrides=['a=3; b=-4']
   overrides=["""
   a=3
   b=-4
   """]

.. note::

   CLI overrides will be passed to :func:`~soleil.load_config` verbatim as a list of strings and will be parsed using an overrides parser that has been restricted to only admit a subset of the Python syntax.



Any useful type admitted by ``overrides``is a dictionary dictionaries:

.. testcode::

   overrides=[{'a':3, 'b':-4}]

All override syntaxes can further combined in a single list:

.. testcode::

   overrides=['a=1', {'b':2}, "c=3;d=4", {'e':5, 'f':6}]



.. rubric:: Evaluation of string overrides

All string overrides are evaluated using a restricted Python parser that supports a subset of Python operations. The contents produces by

.. code-block::

   from soleil import *

are included in the global context when executing the overrides.

Mechanism
------------

In order to support overrides, the soleil pre-processor converts every variable assignment such as

.. code-block::

   a = 1

   class B:
        b = 2

into a call to a special function :func:`_soleil_override`, as follows:

.. code-block::

   a = _soleil_override('a', 1)

   class B:
        b = _soleil_override('b', 2)

When the module executes during a call to :func:`load_config`, the call to :func:`_soleil_override` first checks whether an override was specified for that
variable and returns that override value if so, or the original value otherwise. To do so, :func:`_soleil_override`
matches a variable name path computed for each variable to the names specified in the CLI override strings or keys.
Note that these variable name paths specify the position of each variable relative to root configuration loaded with :func:`load_config`.

Variable name paths are computed using the first argument to :func:`_soleil_override` and the name a given module was loaded to, which is
contained in module-level variable :var:`__soleil_qualname__`.

For example, the variable paths for all variables are given in the comments below when calling ``load_config('<path>/main.solconf')``

.. code-block::

   # main.solconf
   ####################
   # The root configuration has `__soleil_qualname__ = None`
   a = 1               # 'a'
   class B:            # 'B'
       b = 2           # 'B.b'
   C = load('.submod') # 'C', pre-proc converts to `load('.submod', _target='c')`

   # submod.solconf
   ####################
   # The module has `__soleil_qualname__ = 'C'`
   c = 3               # 'C.c'
   d = 4               # 'C.d'



In order to maintain the :var:`__soleil_qualname__` module variables, the soleil pre-processor injects ``_target`` keywords into all simple :func:`load` statements (see the example above).


String overrides parser
--------------------------

Overrides provided as strings are parsed with a special parser that limits the permissible syntax constructs to variable assignments and constants. This offers some protection against erroneous CLI input.
