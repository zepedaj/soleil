Resolvables
===================

.. figure:: ../images/resolvable_cut.png

           Image generated with |DALLE|


.. testsetup::

   from soleil import as_type, resolve, hidden, visible, name, cast

SolConf Modules
-----------------
Solconf modules are regular python modules augmented with extra functionality and stored in solconf package directory hierarchies containing files having ``'.solconf'`` extensions. To load a solconf package, use :func:`soleil.load_config` to load any of the modules in the package root:

.. code-block::

   module = load_config('/path/to/package/root/module.solconf')

.. note:: You can also create a package without explicitly loading a module by passing the package root only: ``load_config('/path/to/package/root')``

By default, calling :func:`load_config` will first create a package with default name ``solconf`` and then create a module within that package using the file's stem name:

.. code-block::

   assert module.__name__ == 'solconf.module'

This new module is registered in python's ``sys`` registry and can be subsequently loaded from any other python package using ``import solconf.module``.

.. rubric:: Solconf sub-modules

Any sub-directory within the package root can be loaded from within a solconf module using the :func:`load` directive:

.. code-block::

   # /path/to/package/root/module.solconf

   submodule = load('.module.submodule')

.. todo:: Make ``load_config`` and ``load`` the same function, deducing whether a module name or filename is passed in based on the string format. Make it possible to call ``load`` from
          regular python modules.


.. rubric:: Module subscripting

Solconf modules that have a promoted member that supports subscripting (e.g., a dictionary or a list) can be accessed directly with a subscript even if the member has not been resolved.

Resolving SolConf Modules
^^^^^^^^^^^^^^^^^^^^^^^^^^
Solconf modules can be resolved by specifying a member with an explicit :func:`as_type` annotation:

.. code-block::

   type:as_type = 'numpy.array'
   object=[0,1,2,3]
   dtype='f'


If no :func:`as_type`-annotated member is provided, the module will instead resolve to a dictionary containing all members:

.. code-block::

   alpha = 1
   beta = 2
   gamma = 3

If no :func:`as_type` member is provided and further a single member is annotated with :func:`promoted`, then the module
will resolve to that member :

.. code-block::

   # package/config.solconf
   alpha = 1
   beta:promoted = 2
   gamma = 3

   # main.py
   assert load_config('package/config.solconf') == 2

Loading a module containing a promoted member will return that member by default:

.. code-block::



    # package/config.solconf

    class Trunk:
       ...


    class NonLinearity:
        ...

    @promoted
    class Model:
        trunk = Trunk
        ...


   # main.py
   assert load(main.solconf) is Model


Classes
--------
Missing

Python Containers
--------------------

Dictionaries, lists, tuples, sets

.. warning:: Currently, container resolution does not preserve resolved instance uniqueness. The non-container members of resolved containers, however, will preserve uniqueness.

.. todo:: Builtins (dict, set, tuple, list) do not resolve to unique instances because they do not support adding an extra attribute (i.e., ``__soleil_resolved__``). Fix this by having the pre-processor output a soleil-specific shim that derives from the container and supports adding extra attributes. The resolver for these shims should output the parent container.

Uniqueness of Resolution
---------------------------------


A resolvable object will only resolve once, meaning that all other references to that resolvable object will point to the same resolved object.

For the case of resolvable classes, this can be overriden by deriving from a given resolvable class:

.. testcode::

    class RslvblA:
        type:as_type = lambda **x: x
        a = 1
        b = 2

    assert resolve(RslvblA) is resolve(RslvblA)

    class RslvblB(RslvblA): pass

    assert resolve(RslvblB) is not resolve(RslvblA)

