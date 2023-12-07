.. _Overriding Configurations:

Overriding Configurations
===========================

.. _variable name paths:

Variable name paths
----------------------

Syntax
------------

The :func:`~soleil.load_config` function supports specifying values that will override those in the loaded configuration by means of its ``overrides`` parameter which must be a list with entries of various possible types (see :class:`OverrideSpec`):

.. code-block::

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



Any useful type admitted by ``overrides`` is a dictionary dictionaries:

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

In order to support overrides, the |soleil| pre-processor converts every variable assignment such as

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
contained in module-level variable :attr:`__soleil_qualname__`.

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



In order to maintain the :attr:`__soleil_qualname__` module variables, the |soleil| pre-processor injects ``_target`` keywords into all simple :func:`load` statements (see the example above).


String overrides parser
--------------------------

Overrides provided as strings are parsed with a special parser that limits the permissible syntax constructs to variable assignments and constants. This offers some protection against erroneous CLI input.
