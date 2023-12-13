
Soleil Pre-Processor
===========================

.. figure:: ../images/soleil_pre_proc.jpg

           Image generated with |DALLE|


Various functionalities provided by |soleil| rely on Python language modifications carried out by the **Soleil pre-processor**. The pre-processor exploits Python's |ast| module to modify the parsed abstract syntax tree extracted from each solconf file before the tree is compiled and executed (see :class:`soleil.loader.ConfigLoader`). While these code modifications should be transparent to the user, it is useful to know what they are.



Pre-processor directives
---------------------------

:func:`load`
^^^^^^^^^^^^^^

When the |load| function is used in a simple assignment such as


.. code-block::

    a = load('.option')


the pre-processor will automatically inject the target name keyword argument to load as follows:

.. code-block::

    a = load('.option', _target='a')

This makes it possible to compute |var name paths| to support CLI overrides.

.. todo:: Add support for overrides with more complex load operations like ``a = load('.option').a.b``.


|promoted|
^^^^^^^^^^^^^^^^^

:attr:`Promoted <soleil.resolvers.module_resolver.promoted>` members are skipped over when building :ref:`variable name paths` and thus the name of the promoted module member needs to be known before the module executes. Extracting this name is part of the job the pre-processor does.


Converting assignments to override checks
-------------------------------------------

The pre-processor converts any variable assignment to a call to the |soleil| override checker:

For example, the code

.. code-block::

   a = 1

is converted to

.. code-block::

   a = _soleil_override('a', 1)

The :func:`~soleil.overrides.overrides._soleil_override` function is not a user-facing function but rather operates under the hood. Its main task is to check the provided CLI overrides and return the matching one, if any, or the original value otherwise. It also adds support for special :class:`~soleil.overrides.overridable.Overridable` values such as :class:`~soleil.overrides.overridable.submodule` and :class:`~soleil.overrides.overridable.choices` that use the user-supplied override value to choose a submodule or value.

Hiding imported members
------------------------

The pre-processor also checks whether any imports are done within a solconf module and adds those names to the list of default-hidden module members that will not be passed as keywords to the module's type call. This can lead to unexpected behavior when a loaded member is re-defined, as this re-defined member will still be hidden::

  import os # os is implicitly hidden

  os = 'new value' # os is still hideen

  os:visible = 'new value' # os is now visible

Explicitly annotating the member with :attr:`visible`, as shown above, overrides the implicit hidden annotation.
