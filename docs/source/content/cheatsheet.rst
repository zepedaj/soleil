.. _cheatsheet:

Cheatsheet
------------------------

As a convenience, all modifiers, utility functions and overridables that are used within `*.solconf` are gathered inside module :mod:`soleil.solconf` and linked here below.



.. _modifiers:

Modifiers
^^^^^^^^^^^^

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


Utility functions
^^^^^^^^^^^^^^^^^^^^^^^^

.. autosummary::


    soleil.utils.id_str
    soleil.utils.root_stem
    soleil.utils.sub_dir
    soleil.utils.derive
    soleil.utils.temp_dir
    soleil.utils.spawn
    soleil.utils.package_overrides
    soleil.rcall.rcall
    soleil.special.resolved.resolved

Overridables
^^^^^^^^^^^^^

.. autosummary::

    soleil.overrides.overridable.submodule
    soleil.overrides.overridable.choices
    soleil.overrides.req.req
