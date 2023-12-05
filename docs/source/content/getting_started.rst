.. _Getting Started:

Getting Started
================

As an example of how to use |soleil|, we will build a system to train a basic classifier. The approach presented is a |soleil| porting of the `CIFAR classification example in the PyTorch website <https://pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html>`_.

.. note:: An installable Python package with code for this and other examples can be found in ``<soleil code root>/soleil_examples``. You can install these examples as follows:

          .. code-block:: bash

            cd <soleil code root>/soleil_examples
            pip install .

          For convenience, ``solconf`` directories are placed inside each example module directory -- note that these do not need to be installed but assume that the *soleil_examples*
          Python packge is installed.

Model and training routine
----------------------------

The Python codebase for the CIFAR classifier training includes two modules.

The first module contains a model:

.. literalinclude:: ../../../soleil_examples/cifar/model.py
                    :linenos:

The second module contains a training routine:

.. literalinclude:: ../../../soleil_examples/cifar/train.py
                    :linenos:


The solconf package
---------------------

A solconf package is just a directory hierarchy containing ``*.solconf`` files that is analogous to a Python package containing modules and nested sub-packages. Unlike a Python package, solconf packages do not need to be installed.

Since our aim is to create a training system, we will create a root configuration called ``train.solconf`` inside folder ``"soleil_examples/cifar/solconf/"``:

.. _train.solconf:

.. rubric:: train.solconf

.. literalinclude:: ../../../soleil_examples/cifar/solconf/train.solconf
                    :linenos:


.. note:: Solconf package **root configurations** are ``*.solconf`` files within the package that are intended to be loaded by the user using |load_config|. All ``*.solconf`` files can be root
          configurations if they resolve (i.e., if any missing :func:`~soleil.overrides.req.req` members are supplied when loading).


The *as_type* member
_____________________________

The first **member** on this package specifies that the package describes a call to the training
routine by means of the line:

.. literalinclude:: ../../../soleil_examples/cifar/solconf/train.solconf
                    :linenos:
                    :start-at: as_type
                    :end-at: as_type
                    :lineno-match:


The ``as_type`` annotation on the ``type`` member indicates to |soleil| that all other non-hidden members will be gathered as keyword variables and passed to this callable. The annotation further lets
|soleil| know that any string value for the member will in fact contain a ``<module>:<entity>`` address that |soleil| will use to retrieve the actual callable. This is only a convenience, and one could also assign to the ``as_type`` member the actual callable directly::

  from soleil_examples.cifar.train import train

  type: as_type = train

The next two members (``net`` and ``optimizer``) also include a nested ``as_type``-annotated member. The first member describes an instance of the
``soleil_examples.cifar.model:Net`` model shown above.

Description attributes vs. instance attributes
__________________________________________________________

The second member -- ``optimizier`` -- describes an instance of PyTorch's `torch.optim:SGD <https://pytorch.org/docs/stable/generated/torch.optim.SGD.html#torch.optim.SGD>`_ optimizer. This description
poses a problem since it requires a call to ``net.parameters()`` to let the optimizer know what parameters we will optimize. But at this point we only have ``net``'s description and not the actual instance. We hence create a special object ``resolved(net)`` that will lazily evaluate all nested attributes, subscripts and calls  to ``net``, resolving these until the entire solconf module is resolved:

.. literalinclude:: ../../../soleil_examples/cifar/solconf/train.solconf
                    :linenos:
                    :start-at: params = resolved(net).parameters()
                    :end-at: params = resolved(net).parameters()
                    :lineno-match:



If we did not need to enable configuration of ``net``, we could have instead assigned the instance of net directly, as is the case for the `CrossEntropyLoss <https://pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html#torch.nn.CrossEntropyLoss>`_ criterion:

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
___________________________________

When describing an object, it is often useful to rely on meta data that is not passed to the ``as_type`` member -- we can do this by annotating members with the special :attr:`~soleil.resolvers.modifiers.hidden` modifier:

.. literalinclude:: ../../../soleil_examples/cifar/solconf/train.solconf
                    :linenos:
                    :start-at: data: hidden = load(".data.default")
                    :end-at: trainloader = data.trainloader
                    :lineno-match:

This tells |soleil| not to pass in the ``data`` member to the module's ``as_type`` member. The dependent variable ``trainloader``, however, will be passed in.

|Soleil| will by default mark as hidden any member with a name prefixed by an underscore character ``'_'``. When an ``'_'``-prefixed name is expected by the ``as_type``  member, the variable can explicitly be marked as visible::

   _param:visible = ...

Alternatively, a different name can be used for the member and the keyword argument by means of the :attr:`~soleil.resolvers.modifiers.name` modifier that specifies the ``as-type`` keyword argument name::

  param:name('_param') = ...


Loading sub-modules
____________________

Since a description of the data used to train and test the model is complex and a concern of its own, we create it in a separate solconf module that we |load| using:

.. literalinclude:: ../../../soleil_examples/cifar/solconf/train.solconf
                    :linenos:
                    :start-at: data: hidden = load(".data.default")
                    :end-at: data: hidden = load(".data.default")
                    :lineno-match:

The path provided to the |load| function follows rules similar to module paths provided to Python ``import`` statements. The main difference is that absolute paths will refer to top-level sub-modules within the same package. In this case, since the root config ``"train.solconf"`` is at the root of the package, then ``load(".data.default")`` and ``load("data.default")`` would both load the same sub-module.



Inheriting descriptions
_________________________

The data description solconf module ``"data.default"`` contains the following code:

.. literalinclude:: ../../../soleil_examples/cifar/solconf/data/default.solconf
                    :linenos:

The module contains two base descriptions -- ``dataset`` and ``dataloader`` -- that will be derived by the training and testing datasets and dataloader descriptions. These base descriptions on their own cannot be resolved because they contain unspecified required members::

  class dataset:
    ...
    train = req()
    ...


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

.. rubric:: Differentiating instantiations

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

Inheriting from modules -- *promoted* and *spawn*
------------------------------------------------------
Pending
