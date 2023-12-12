
Modifier syntax
----------------------

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

The modifiers below can be used in different contexts. For convenience they are all included in the base :mod:`soleil.solconf` module and included automatically with ``from soleil.solconf import *``.

(See :ref:`modifiers` for a list of all available modifiers)
