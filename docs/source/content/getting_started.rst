General
============


Soleil is a configuration system that allows you to specify arbitrary python objects in terms of reconfigurable meta parameters. For example, a set of presentation colors can be specified in terms
of the following meta-parameters organized into a python class:

.. testcode::

   class model:
        type:as_type = 'torch.nn.Linear'


Meta parameters are resolved into objects used in target programs:

.. testcode::

   assert resolve(presentation_colors) == {'foreground':'blue', 'background':'yellow', 'font':'black'}

Loading a soleil configuration

Solconf files can be seen as specification of meta parameters that will then be resolved into an actual paramtere

Solconf modules
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

File syntax
--------------


A resolvable object will only resolve once, meaning that all other references to that resolvable object will point to the same resolved object.

For the case of resolvable classes, this can be overriden by deriving from a given resolvable class:

.. testcode::

    class RslvblA:
        type:type_arg = lambda **x: x
        a = 1
        b = 2

    assert resolve(RslvblA) is resolve(RslvblA)

    class RslvblB(RslvblA): pass

    assert resolve(RslvblB) is not resolve(RslvblA)


Modifiers
===========

Modifiers can be chained using a tuple:

.. testcode::

   class A:
       a:(hidden,name('__a__'),cast(int)) = '3' 

Modifiers can  can also be applied to classes using the following syntax:

.. testcode::

    A:hidden
    
    class A:
        ...
        
Modifiers are automatically inherited but can be overriden in derived classes, while still inheriting the value:

.. testcode::

    class A:
        a:hidden = 1
        
    class B(A):
        a:visible # TODO: need to implement a 'squash' version of merge where old values get overwritten if available.


Pre-processor
========================================


Imported name hidding:
----------------------------


The pre-processor will automatically hide any imported names, regardless of the level at which the import happens:

.. code-block::

    # Will be automatically hidden in solconf modules:
    
    from numpy import array
    from pandas import *
    from scipy import linalg as la
    
    # We would like to resolve this
    from my_solconf_module import important_parameter
    
    class A:
        import numpy as np # Name np is hidden globally in the module
    
    
Automatically-hidden imported variables can be made visible by assigning to a new variable or with an explicit annotation:

.. code-block::

    # Made visible by assignment to new name 
    also_visible = important_parameter

    # Original name made visible with modifier type hint
    important_parameter:visible
      
  
Converting assignments to :class:`Ref`
-----------------------------------------

In order to support :ref:`CLI overrides`, assignments involving expressions with named variables will be substituted by expressions instead having *references* to those named variables. This is so that any CLI override of a variable is propagated to any expression that depends on that variable. Function calls will also be replaced by calls that first resolve the input parameters. In the example below, when overriding ``var``, the new value will be correctly used in the two dependent expressions:

.. code-block::

   # Original code
   var = 1
   expr_1 = var
   expr_2 = fxn(var)

.. code-block::

   # Equivalent modified code produced by the pre-processor
   # that supports CLI overrides of `var`
   var = 1
   expr_1 = Ref('var')
   expr_2 = refs_call(fxn, Ref('var'))
