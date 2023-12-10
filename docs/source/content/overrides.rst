.. _Overriding Configurations:

Overriding Configurations
===========================

.. figure:: ../images/overrides_cut.jpg

           Image generated with |DALLE|


Whether a soleil described object is loaded from a Python script or resolved following a :ref:`CLI <Automatic CLI>` command, under the hood, the processing is carried out by a call to |load_config| of the form

.. code-block::

   resolved_obj = load_config('./root_config.solconf', overrides=[...])

The value provided to the *overrides* parameter is always a list that admits target **variable name path**/value pairs in multiple possible formats (see :class:`~soleil.overrides.overrides.OverrideSpec`).

For example, entries of ``overrides`` can be strings in various Python-syntax-compatible forms, possibly specifying more than one override in each entry:

.. testcode::

   overrides=['a=3', 'b=[1,2]', 'c={1,2}', 'd=(1,2)']
   overrides=['a="xyz"; b=1e-5']
   overrides=["""
   a=b'xyxy'
   b={1:-4,'a':5}
   """]

.. note::

   Overrides provided from the CLI are always in string format -- they will be evaluated using a special Python parser.


Another useful type admitted as an entry of ``overrides`` is a dictionary of Python objects:

.. testcode::

   overrides=[{'a':3, 'b':-4}]

All override syntaxes can further be combined in a single list:

.. testcode::

   overrides=['a=1', {'b':2}, "c=3;d=4", {'e':5, 'f':6}]


.. _variable name paths:

Variable name paths
----------------------

The target **variable name path** of an override specifies the position of the target relative to the root configuration. Consider, as an example, the following part of the :ref:`train.solconf` configuration introduced in the :ref:`Getting Started` section:

.. literalinclude:: ../../../soleil_examples/cifar/solconf/train.solconf
                    :linenos:
                    :start-at: class optimizer:
                    :end-at: momentum = 0.9
                    :lineno-match:

Since the *optimizer* class is defined at the highest level in the *root config*, the learning rate parameter can be modified using an override of the form::

  'optimizer.lr=0.002'
  {'optimizer.lr': 0.002}

In general, keys for members of a (nested) class in the root config will be the dot-separated `class qualified name <https://docs.python.org/3/glossary.html#term-qualified-name>`__ and variable name. So, given the following class with members that are also object descriptors (*assumed defined in the root config*)

.. code-block::

   class model:
      type: as_type = "soleil_examples.cifar.model:Net"

      class backbone:
         type: astype = 'torch.nn:Linear'
         in_features = 10
         out_features = 20

one can modify the number of output features using

.. code-block::

   'model.backbone.out_features=30'

Variable name paths for *loaded members* are formed accordingly by dot-joining the variable name path of the load target variable, and that of the override target (as if it were in the root config). For example, given the following line from root config :ref:`train.solconf`

.. literalinclude:: ../../../soleil_examples/cifar/solconf/train.solconf
                    :linenos:
                    :start-at: data: hidden = load(".data.default")
                    :end-at: data: hidden = load(".data.default")
                    :lineno-match:

the member *root* of class *dataset*(defined in loaded file :ref:`data/default.solconf <default.solconf>`) can be overriden with the following overrides::

  "data.dataset.root='/my/new/root'"
  {'data.dataset.root': '/my/new/root'}


Evaluation time and context
------------------------------------

All overrides make use of |AST| magic to ensure that the override is applied **at the moment of the target variable's definition**. This ensures that any other variables that depend on the value of the overriden member themselves see the overriden value. See :ref:`Mechanism` below for the approach used to do this.

Currently, the **globals** dictionary used when evaluating the value of the override is empty. This means that only constants can be assigned as override values. Some extra flexibility is added by means of the special overrideables :class:`~soleil.overrides.overridable.submodule` and :class:`~soleil.overrides.overridable.choices`.

.. todo:: 1) Inject ``from soleil import *`` into to overrides evaluation globals. 2) Add a ``ref(<var path>)`` method that resolves to the description of a given path. Resolved attributes can be accessed using ``resolved(ref(<var path>))``.

.. _Mechanism:

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
