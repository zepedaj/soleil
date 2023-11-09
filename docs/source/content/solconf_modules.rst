Solconf Modules
-----------------

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
