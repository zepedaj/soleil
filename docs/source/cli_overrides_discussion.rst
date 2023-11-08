Ref-based CLI overrides
==========================

In this approach, the pre-processor changes all assignments of variables to assignments of references to variables
using :class:`Ref` objects that are aware of the nested content resolution depending on whether they are assigned
at the global level or a class level:

.. code-block::

   # Original code
   a = b
   class A:
       c = 1
       d = c

   # Pre-process substituted code.
   a = Ref('b')
   class A:
       c = 1
       d = Ref('A.c')

The above approach breaks a lot of built-in python function evaluation and operator support. Function evaluation is addressed
by a pre-processor substitution of all functions by references to functions using :func:`ref_call`:

.. code-block::

   # Original code
   fxn(a, b)

   # Pre-process substituted code.
   ref_call(Ref('fxn'), Ref('a'), Ref('b'))

Operator support is only partially addressed by overloading arithmetic operators. Excluded from the overloads, however,
are comparison operators, because including these would break the :calss:`Resolver` selection mechanism:  Comparisons involving :class:`Ref` would return :class:`Ref` objects.
Attempting to address this by resolving the :class:`Ref` at comparison time would defeat the purpose of :class:`Ref`, which is support for late assignment.

The above makes programming unintuitive, and this is further exacerbated by the need to use the special implenmentation :func:`isinstance_` of the builtin :func:`isinstance` when
inspecting objects that might be :class:`Ref` instances.

This approach supports :class:`submodule` which is also a special :class:`Settable` kind of :class:`Ref`.

Pre-processor based CLI overrides
===================================

The pre-processor keeps track of the current node qualified name, and substitutes the value of the node if it matches the CLI name:

No need for :func:`ref_call` or :func:`Ref` operator overloading.

Will fail if assignment depends on module content created after the assignment point.

Support for :class:`submodule` would be done by making :class:`submodule` a special pre-processor keyword with
the chosen module parameter substitued by the pre-processor.

Override at assignment time
---------------------------

.. code-block::

    # Original code
    a = 1
    class B:
        b = 1

    # Pre-processor substituted code
    # for cli override "B.b=${B_b_override_str}"
    class B:
        b = eval(B_b_override_str) # In local context
        b = eval(B_b_override_str, globals()) # In global context

The local content approach might lead to unexpected results, as whether a variable defined in the class
is used for resolution depends on whether that variable is defined before or after the assignment. While
this is standard in Python, it is not evident from the CLI, where the variable assignment order is not
visible.

Override after container creation
----------------------------------

Local variables in the ``class B`` block that depend on ``B.b`` will have the wrong value.

.. code-block::

    # Original code
    a = 1
    class B:
        b = 1

    # Pre-processor substituted code
    # for cli override "B.b=${B_b_override_str}"
    class B:
        b = 1
    B.b = eval(B_b_override_str, globals()) # Always in global context

Pit-falls
==========

Doubly-assigned values will not be overriden correctly.

.. code-block::

    a = 1
    a = 2
