
Modifier syntax
----------------------

:class:`~soleil.resolvers.modifiers.Modifiers` are special dictionary sub-classes that are used to annotate members of resolvable classes and modules and thus change their behavior.

Composing, decoration and inheritance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modifiers can be composed using a tuple:

.. testcode::

   from soleil.solconf import *

   class A:
       a:(hidden,name('__a__'),cast(int)) = '3'

They can also be applied to member classes (and any to-be-defined variable) using the following syntax:

.. testcode::

   from soleil.solconf import *

   A:hidden

   class A:
       ...

Alternatively, most modifiers support usage as a class decorator. The previous example could hence be rewritten as follows:

.. testcode::

   from soleil.solconf import *

   @hidden
   class A:
       ...

Modifiers are automatically inherited but can be overriden in derived classes, while still inheriting the parent's value:

.. testcode::

   from soleil.solconf import *

   class A:
        type: as_type = lambda a: a+1
        a:visible = 1

   class B(A):
        type: as_type = lambda : 2
        a:hidden

    assert B.a == 1

This can come in handy when we wish to hide inherited values in a derived class, as shown in the example above.



Available modifiers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For convenience, we have included all available modifiers in module  :mod:`soleil.solconf` -- a full list can be seen in the :ref:`modifiers` section of the :ref:`cheatsheet`.
