.. _Getting Started:

Getting Started
================

.. figure:: ../images/rising_sun_cut.jpg

           Image generated with |DALLE|

As an example of how to use |soleil|, we will build a system to train a basic classifier. The approach presented is a |soleil| porting of the `CIFAR classification example in the PyTorch website <https://pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html>`_.

.. note:: An installable Python package with code for this example can be found in ``<soleil code root>/soleil_examples``. You can install these examples as follows:

          .. code-block:: bash

            cd <soleil code root>/soleil_examples
            pip install .

          For convenience, ``solconf`` directories are placed inside each example module directory -- note that these do not need to be installed but assume that the *soleil_examples*
          Python package is installed.

Model and training routine
----------------------------

One advantage of Soleil is that it allows you to better separate

* the code for the various components of your system (e.g., your model) from
* the code that assembles these components into a single system.

For our CIFAR classifier example, there are two main components, *1)* the model and *2)* the training routine. We include the two modules containing these below, although the actual implementation beyond function and class initialization parameters is not important for this example.

Note that |soleil| assumes that modules with components such as these are installed (or at least in the Python path) and accessible with standard Python import statements.

.. literalinclude:: ../../../soleil_examples/cifar/model.py
                    :linenos:
                    :caption: soleil_examples/cifar/model.py


.. literalinclude:: ../../../soleil_examples/cifar/train.py
                    :linenos:
                    :caption: soleil_examples/cifar/train.py


The solconf package
---------------------

A solconf package is just a directory hierarchy containing ``*.solconf`` files that is analogous to a Python package containing modules and nested sub-packages. Unlike a Python package, solconf packages do not need to be installed.

Since our aim is to create a training system, we will create a root configuration called ``train.solconf`` inside our solconf package folder:

.. _train.solconf:

train.solconf
---------------

.. literalinclude:: ../../../soleil_examples/cifar/solconf/train.solconf
                    :linenos:
                    :caption: soleil_examples/cifar/solconf/train.solconf


.. note:: Solconf package **root configurations** are ``*.solconf`` files within the package that are intended to be loaded by the user using |load_config|. All ``*.solconf`` files can be root
          configurations if they resolve (i.e., if any missing :func:`~soleil.overrides.req.req` members are supplied when loading).


The *as_type* member
-----------------------------------------------------

The first **member** on this package specifies that the package describes a call to the training
routine by means of the line:

.. literalinclude:: ../../../soleil_examples/cifar/solconf/train.solconf
                    :linenos:
                    :start-at: as_type
                    :end-at: as_type
                    :lineno-match:




The ``as_type`` annotation on the ``type`` member indicates to |soleil| that *1)* the member will contain a callable that will resolve the module and that *2)* all other non-hidden module members will be gathered, resolved and passed  to this callable as keyword arguments. If, as in this case, the member's value is a string with format ``<module>:<entity>``,  the ``as_type`` modifier will further  retrieve the actual callable and assign it the the ``as_type`` member. Note that this is only a convenience, and one could also assign to the ``as_type`` member the actual callable directly::

  from soleil_examples.cifar.train import train

  type: as_type = train


.. note:: Annotations such as ``as_type`` are called :ref:`modifiers <Modifiers>` in |soleil| parlance. Other common modifiers include ``hidden`` and ``promoted``. Note that modifiers can be applied to non-declared variables and classes and follow standard Python annotation inheritance rules::

          undefined_var:hidden

          UndefinedClass:hidden # The class is only defined starting in the next line
          class UndefinedClass:
             b = 1

          @hidden
          class MyDerivedClass(UndefinedClass): # The hidden modifier is not inherited
             b:hidden # The inherited `b` is hidden in the derived class

       As shown in the example for ``MyDerivedClass``, as a convenience, modifiers can also be applied to classes by using them as class decorators. Note that derived classes can hide inherited members without changing their value.



  
The next two members (``net`` and ``optimizer``) also include a nested ``as_type``-annotated member. The first member describes an instance of the
``soleil_examples.cifar.model:Net`` model shown above.

Description attributes vs. instance attributes
-----------------------------------------------------

Continuing our analysis of :ref:`train.solconf`, the second member -- ``optimizier`` -- describes an instance of PyTorch's `torch.optim:SGD <https://pytorch.org/docs/stable/generated/torch.optim.SGD.html#torch.optim.SGD>`_ optimizer. This description
poses a problem since instantiating the optimizer requires a call to ``net.parameters()`` to let the optimizer know what parameters we will optimize. But at this point we only have ``net``'s description and not the actual instance, so we cannot call ``net.parameters()``. We hence create a special object ``resolved(net)`` that will lazily evaluate all nested attributes, subscripts and calls  to ``net``, resolving these until the entire solconf module is resolved:

.. literalinclude:: ../../../soleil_examples/cifar/solconf/train.solconf
                    :linenos:
                    :start-at: params = resolved(net).parameters()
                    :end-at: params = resolved(net).parameters()
                    :lineno-match:


If we did not need to enable configuration of ``net``, we could have instead assigned the instance of net directly, obviating the need for the lazy evaluation trick via ``resolved`` described above.
Member `criterion`, for example, is initialized directly to an instance of `CrossEntropyLoss <https://pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html#torch.nn.CrossEntropyLoss>`_:

.. literalinclude:: ../../../soleil_examples/cifar/solconf/train.solconf
                    :linenos:
                    :start-at: criterion = nn.CrossEntropyLoss()
                    :end-at: criterion = nn.CrossEntropyLoss()
                    :lineno-match:


For completeness, a possible configurable description of ``criterion`` could instead be::

   class criterion:
        type:as_type = 'torch.nn:CrossEntropyLoss'
        label_smoothing = 0.0
        ignore_index = -100




Hidden, visible and named members
-----------------------------------------------------

When describing an object, it is often useful to rely on meta data that is not passed to the ``as_type`` member -- we can do this by annotating members with the special :attr:`~soleil.resolvers.modifiers.hidden` modifier:

.. literalinclude:: ../../../soleil_examples/cifar/solconf/train.solconf
                    :linenos:
                    :start-at: data: hidden = load(".data.default")
                    :end-at: trainloader = data.trainloader
                    :lineno-match:

This tells |soleil| not to pass in the ``data`` member to the module's ``as_type`` member. The dependent variable ``trainloader``, however, will be passed in.

|Soleil| will by default mark as hidden any member with a name prefixed by an underscore character ``'_'``. When an ``'_'``-prefixed name is expected by the ``as_type``  member, the variable can explicitly be marked as visible::

   _param:visible = ...

Alternatively, a different name can be used for the member and the ``as_type`` keyword argument by means of the :attr:`~soleil.resolvers.modifiers.name` modifier that specifies the ``as_type`` keyword argument name::

  param:name('_param') = ...


Loading sub-modules
-----------------------------------------------------

Since a description of the data used to train and test the model is complex and a concern of its own, we create it in a separate solconf module that we load with the |load| function:

.. literalinclude:: ../../../soleil_examples/cifar/solconf/train.solconf
                    :linenos:
                    :start-at: data: hidden = load(".data.default")
                    :end-at: data: hidden = load(".data.default")
                    :lineno-match:

The path provided to the |load| function follows rules similar to module paths provided to Python ``import`` statements. The main difference is that absolute paths will refer to top-level sub-modules within the same package. In this case, since the *data* sub-package and the root config *train.solconf* are both at the root of the package, then ``load(".data.default")`` and ``load("data.default")`` would both load the same sub-module.



Inheriting descriptions
-----------------------------------------------------

The data description solconf module ``"data.default"`` contains the following code:


.. _default.solconf:

.. literalinclude:: ../../../soleil_examples/cifar/solconf/data/default.solconf
                    :linenos:
                    :caption: soleil_examples/cifar/solconf/data/default.solconf

The module contains two template descriptions -- ``dataset`` and ``dataloader`` -- that will be derived by the training and testing dataset and dataloader descriptions. These template descriptions on their own cannot be resolved because they contain unspecified required members::

  @hidden
  class dataset:
    ...
    train = req()
    ...

  @hidden
  class dataloader:
    ...
    dataset = req()
    shuffle = req()
    ...

The training and testing datasets inherit all the non-required members and overload the required members, making them resolvable::

  class trainset(dataset):
      train = True

  class testset(dataset):
      train = False

  class trainloader(dataloader):
      dataset = trainset
      shuffle = True

  class testloader(dataloader):
      dataset = trainset
      shuffle = False

Differentiating instantiations
-------------------------------

A given |soleil| resolvable (e.g., ``trainset`` above) always resolves to the same instance of the description::

  from soleil import resolve

  obj1 = resolve(trainset)
  obj2 = resolve(trainset)

  assert obj1 is obj2

This makes it possible to pass the same object to multiple ``as_type`` members.

When different instances are required, one needs to derive a description for each instance::

  obj1 = resolve(trainset)

  class trainset2(trainset): pass

  obj2 = resolve(trainset2)

  assert obj1 is not obj2

This can also be done with the convenience method ``derive``::

  trainset2 = derive(trainset1)

  obj1 = resolve(trainset)
  obj2 = resolve(trainset2)

  assert obj1 is not obj2

Module inheritance with *promoted* and *spawn*
------------------------------------------------------
Pending
