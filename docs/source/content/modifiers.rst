
.. _Modifiers:

Modifiers
-----------

:class:`~soleil.resolvers.modifiers.Modifiers` are special dictionary sub-classes that are used as annotations in |soleil| object descriptions to change member behaviors.

Chaining, decoration and inheritance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modifiers can be chained using a tuple:

.. testcode::

   from soleil.solconf import *

   class A:
       a:(hidden,name('__a__'),cast(int)) = '3'

Most modifiers can also be applied to classes using the following syntax:

.. testcode::

   from soleil.solconf import *

   A:hidden

   class A:
       ...

Modifiers are automatically inherited but can be overriden in derived classes, while still inheriting the value:

.. testcode::

   from soleil.solconf import *

   class A:
       a:hidden = 1

   class B(A):
       a:visible # TODO: need to implement a 'squash' version of merge where old values get overwritten if available.

Available modifiers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The modifiers below can be used in different contexts. For convenience they are all included in the base :mod:`soleil` module and included automatically with ``from soleil.solconf import * ``.

.. rubric:: Modifers for class and module members

.. autosummary::

   soleil.resolvers.modifiers.hidden
   soleil.resolvers.modifiers.visible
   soleil.resolvers.modifiers.name
   soleil.resolvers.modifiers.cast
   soleil.resolvers.modifiers.noid
   soleil.resolvers.class_resolver.as_type
   soleil.resolvers.class_resolver.as_args


.. rubric:: Modifers for module members

.. autosummary::

   soleil.resolvers.module_resolver.as_run
   soleil.resolvers.module_resolver.promoted
   soleil.resolvers.module_resolver.resolves
