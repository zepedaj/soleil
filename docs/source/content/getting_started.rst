.. _Getting Started:

Getting Started
================

.. figure:: ../images/rising_sun_cut.jpg

           Image generated with |DALLE|

As an example of how to use |soleil|, we will build a system to train a basic classifier. The approach presented is a |soleil| porting of the `CIFAR classification example in the PyTorch website <https://pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html>`_.

.. note:: An installable Python package with code for this example can be found in source sub-directory *<soleil code root>/soleil_examples*. You can install these examples as follows:

          .. code-block:: bash

            cd <soleil code root>/soleil_examples
            pip install .

          For convenience, `./solconf` sub-directories are placed inside each example module directory.

Model and train/eval routines
-------------------------------------------------------

The CIFAR classifier example consists of three main components, *1)* the model, *2)* the training routine and *3)* the evaluation routine. We show the function and initializer signatures for these components below -- the details of the implementation beyond the parameter names are not necessary when building solconf modules.

Note that, as is common, the train and eval routines share some commone parameters.

.. note:: |soleil| assumes that modules with components such as these are installed (or at least in the Python path) and accessible with standard Python import statements.

.. literalinclude:: ../../../soleil_examples/cifar/conv_model.py
                    :linenos:
                    :start-at: class Net(nn.Module):
                    :end-at: def __init__(self):
                    :lineno-match:
                    :caption: soleil_examples/cifar/conv_model.py


.. literalinclude:: ../../../soleil_examples/cifar/train.py
                    :linenos:
                    :start-at: def train(net, trainloader, optimizer, criterion, path):
                    :end-at: def train(net, trainloader, optimizer, criterion, path):
                    :lineno-match:
                    :caption: soleil_examples/cifar/train.py

.. literalinclude:: ../../../soleil_examples/cifar/eval.py
                    :linenos:
                    :start-at: def eval(testloader, net, path):
                    :end-at: def eval(testloader, net, path):
                    :lineno-match:
                    :caption: soleil_examples/cifar/eval.py



The solconf package
---------------------

A solconf package is a directory hierarchy containing `*.solconf` files that is analogous to a Python package containing modules and nested sub-packages. When loaded, the package's `*.solconf` files will be instantiated as :class:`~soleil.resolvers.module_resolver.SolConfModule` objects. Unlike a Python package, solconf packages do not need to be installed -- their **root configurations** can be loaded by file path using |load_solconf|.

.. note:: Soleil package **root configurations** are `*.solconf` files within the package that are intended to be loaded by the user using |load_solconf|. All `*.solconf` files can be root
          configurations if they resolve (i.e., if overrides for all :func:`~soleil.overrides.req.req` members are supplied when loading).

Since our aim is to create a training system, we will create a root configuration called `train.solconf` inside our solconf package folder:

.. _train.solconf:

**train.solconf**
------------------------------

.. _file train.solconf:

.. literalinclude:: ../../../soleil_examples/cifar/solconf/train.solconf
                    :linenos:
                    :caption: soleil_examples/cifar/solconf/train.solconf


The *as_type* member
-----------------------------------------------------

The first **member** on this package specifies that the package describes a call to the training
routine by means of the line:

.. literalinclude:: ../../../soleil_examples/cifar/solconf/train.solconf
                    :linenos:
                    :start-at: as_type
                    :end-at: as_type
                    :lineno-match:




The ``as_type`` annotation on the ``type`` member indicates to |soleil| that *1)* the member will contain a callable that will resolve the module and that *2)* all other non-**hidden** module members will be gathered, resolved and passed  to this callable as keyword arguments. If, as in this case, the member's value is a string with format ``<module>:<entity>``,  the ``as_type`` modifier will further  retrieve the actual callable and assign it the the ``as_type`` member. Note that this is only a convenience, and one could also assign to the ``as_type`` member the actual callable directly::

  from soleil_examples.cifar.train import train

  type: as_type = train


.. note:: Annotations such as ``as_type`` and ``hidden`` are called **modifiers** in |soleil| parlance and change the behavior of the member they annotate. See the :ref:`modifier syntax` section for more details on their usage or the :ref:`cheatsheet's modifiers <modifiers>` section for a full list of available modifiers.

  
The next two members (``net`` and ``optimizer``) also include a nested ``as_type``-annotated member. The first member describes an instance of the
``soleil_examples.cifar.model:Net`` model shown above.

Description attributes vs. instance attributes
-----------------------------------------------------

Continuing our analysis of :ref:`train.solconf`, the second member -- ``optimizer`` -- describes an instance of PyTorch's `torch.optim:SGD <https://pytorch.org/docs/stable/generated/torch.optim.SGD.html#torch.optim.SGD>`_ optimizer. This description
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



The *submodule* and *choices* overridables
--------------------------------------------------------

One common situation in machine learning experiments it the need to swap out one component -- the model

.. literalinclude:: ../../../soleil_examples/cifar/solconf/train.solconf
                    :linenos:
                    :start-at: class net:
                    :end-at: type: as_type = "soleil_examples.cifar.conv_model:Net"
                    :lineno-match:

for example --  by a new variant. Doing so without modifying existing solconf files is useful, and |submodule| offers a way to do so: One first creates a new `*.solconf` file for the new variant and places all such variants in the same subpackage.

For example, we can place two model descriptions *models/conv.solconf* and *models/fc.solconf* inside sub-package  *models/*. Using the special load variant |submodule| in

.. code-block::

   net = submodule('.models', 'conv')

tells soleil to load the model description in soleil module ``.models.conv`` if no override is provided, and to otherwise use the override value as the module name. As example, one could load the fully connected variant of the model using

.. code-block:: bash

   $ solex train.solc net='"fc"'

Another useful function similarly providing special overridable abilities is |choices| -- it works like |submodule| but lets you explicitly provide the value for each string key as opposed to requiring these to be names of sub-modules in a specific sub-package.

As an example, we can rewrite the |submodule|-based model selection mechanism above with |choices| as follows:

.. code-block::

   net = choices(
           {'conv': load('.models.conv'), 'fc': load('.models.fc')},
           'conv'
         )


**train2.solconf**
-----------------------

In order to run evaluations on the trained model, we need to build an `eval.solconf` configuration. Since the :func:`eval` and :func:`train` functions both share common parameters, it makes sense to inherit some of these parameters from the train configuration when building the eval configuration. To support this, we will modify our |train.solconf| configuration, wrapping all the parameters in a class that we can later inherit from (the lines modified relative to |train.solconf| are highlighted):

.. _file train2.solconf:

.. literalinclude:: ../../../soleil_examples/cifar/solconf/train2.solconf
                    :linenos:
                    :caption: soleil_examples/cifar/solconf/train2.solconf
                    :emphasize-lines: 7,8,18,19,23

Promoted module classes
------------------------------

The **@promoted** decorator applied to this class (see the first two highlighted lines in |train2.solconf|) is a syntactic convenience that ensures that, when loading ``train2.solconf`` using, e.g.,

.. code-block::

   load_solconf("./train2.solconf")

the returned value continues to be whatever object was described in the module -- in this case the output of function ``train(...)`` -- as opposed to the dictionary ``{'_':train(...)}``.

Similarly, when loading a submodule within a solconf file,

.. code-block::

   train_class = load("./train2.solconf")

will return the promoted class "_" as opposed to the the solconf module of type :class:`~soleil.resolvers.module_resolver.SolConfModule`.

In general, promotion will make the syntax for CLI overrides more natural and the output of sub-modules loaded within solconf files more intuitive.

.. note:: It is good practice to always wrap the members of a module in a promoted class. Doing so makes it possible to derive that module to create new root configurations and improves override syntax. Note that all module members outside the class are in effect hidden.

Going back to our example in |train2.solconf|, wrapping the contents of the module in a class created the following problem: the local context of the nested ``optimizer`` class can no longer see the ``net`` variable defined in the local context of the containing class ``_``. We address that problem by defining a global variable ``_params`` (implicitly hidden due to the underscore prefix -- and because it is part of the globals and not the class's locals) in the parent local context, where ``net`` is visible, and using that in the nested class (see the last three highlighted lines in |train2.solconf|).

**eval.solconf**
------------------------------

We can now use |train2.solconf| as a base to build an eval configuration:

.. _file eval.solconf:

.. literalinclude:: ../../../soleil_examples/cifar/solconf/eval.solconf
                    :linenos:
                    :caption: soleil_examples/cifar/solconf/eval.solconf

Module inheritance with *spawn*
------------------------------------------------------

The configuration consists of a promoted class that derives from a ``spawned`` module:

.. literalinclude:: ../../../soleil_examples/cifar/solconf/eval.solconf
                    :linenos:
                    :start-at: @promoted
                    :end-at: class _(_train := spawn(".train2")):

The spawn :func:`~soleil.utils.spawn` assumes that it receives a path to a module with a promoted class. It will then create a new package and load spawned module in that package, passing in the process any overrides that were specified within the source package. The returned class is hence part of a new package and will be a different class than if the spawned module were instead loaded (e.g., using ``load(".train2")``). Using spawn as opposed to ``load``  allows overrides to be specified more naturally, while ensuring that overrides continue to be applied at :ref:`variable definition time <eval time and context>`.

.. todo:: Add a ``+=`` assignment operator that allows overrides to be applied *after* the target description (read ``class`` or module) is created. This will not support links to dependent variable.
