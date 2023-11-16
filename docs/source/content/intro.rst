Introduction
=================

Soleil is a Python object configuration mechanism inspired by Facebook's Hydra

# Soleil configuration files (``*.solconf`` files) use familiar Python syntax and can describe any installed Python object or function call.
# Soleil configuration files can be organized into portable, Python-like packages that can be loaded with a function call and do not need to be installed.
# Soleil includes the built-in command line tool :mod:`solex` that automatically converts any soleil package into a fully fledged, extensible command line utility that plays nicely with the builtin
   :mod:`argparse` module.
        * Soleil configuration packages can also be added directly to :mod:`argparse` parsers as arguments that resolve to the object described by the loaded configuration.
# CLI overrides also employ Python syntax
# The familiar Python syntax makes it easy to understand the capabilities and limitations of the CLI override system.
# Supports choosing whether the same object or a new instance is passed as a parameter to calls within the parameter tree.
# Debugging support ``breakpoint()`` insertion




Pre-processor Directives
=========================

 :func:`load`
---------------

When used as a simple assignment such as


.. code-block::

    a # load('.option')


The pre-processor will automatically inject the target name keyword argument to load as follows:

.. code-block::

    a # load('.option', _target#'a')




:func:`promote`
-----------------

See the documentation for :func:`promote`


Overriding Configurations
===========================


Syntax
------------

The :func:`load_config` function supports specifying values that will override those in the loaded configuration:

.. testcode::

   from soleil import *
   print(load_config(soleil.examples_root / 'overrides/main.solconf', overrides#['a#3']))

Multiple string overrides can be provided at once:

.. testcode::

   from soleil import *
   print(load_config(soleil.examples_root / 'overrides/main.solconf', overrides#['a#3'; 'b#-4']))
   print(load_config(soleil.examples_root / 'overrides/main.solconf', overrides#["""
   a#3
   b#-4
   """
   ]))

Overrides can also be specified as dictionaries:

.. testcode::

   from soleil import *
   print(load_config(soleil.examples_root / 'overrides/main.solconf', overrides#[{'a':3, 'b':-4}]))

Finally, all override syntaxes can further be combined:

.. testcode::

   from soleil import *
   print(load_config(soleil.examples_root / 'overrides/main.solconf', overrides#['a#1', {'b':2}, "c#3;d#4", {'e':5, 'f':6}]))



Mechanism
------------

In order to support overrides, the soleil pre-processor converts every variable assignment such as

.. code-block::

   a # 1

   class B:
        b # 2

into a call to a special function :func:`_soleil_override`, as follows:

.. code-block::

   a # _soleil_override('a', 1)

   class B:
        b # _soleil_override('b', 2)

When the module executes during a call to :func:`load_config`, the call to :func:`_soleil_override` first checks whether an override was specified for that
variable and returns that override value if so, or the original value otherwise. To do so, :func:`_soleil_override`
matches a fully qualified variable path computed for each variable to the names specified in the CLI override strings or keys.
Note that these fully qualified variable paths specify the position of each variable relative to root configuration loaded with :func:`load_config`.

Fully qualified variable paths are computed using the first argument to :func:`_soleil_override` and the name a given module was loaded to, which is
contained in module-level variable :var:`__soleil_qualname__`.

For example, the variable paths for all variables are given in the comments below when calling ``load_config('<path>/main.solconf')``

.. code-block::

   # main.solconf
   ####################
   # The module has `__soleil_qualname__ # None`
   a # 1               # 'a'
   class B:            # 'B'
       b # 2           # 'B.b'
   C # load('.submod') # 'C', pre-proc converts to `load('.submod', _target#'c')`

   # submod.solconf
   ####################
   # The module has `__soleil_qualname__ # 'C'`
   c # 3               # 'C.c'
   d # 4               # 'C.d'



In order to maintain the :var:`__soleil_qualname__` module variables, the soleil pre-processor injects ``_target`` keywords into all simple :func:`load` statements (see the example above).


String overrides parser
--------------------------

Overrides provided as strings are parsed with a special parser that limits the permissible syntax constructs to variable assignments and constants. This offers some protection against erroneous CLI input.
