.. _Automatic CLI:

Automatic CLI
===============


.. figure:: ../images/solex/mission_cut.jpg

           Image generated with |DALLE|


Soleil offers three main ways to create CLIs from solconf files:

    #. by means of the builtin |solex| script that enables calling any solconf file directly,
    #. by means of the |@solex| decorator that turns any function into a CLI,
    #. or by adding an argument of type |SolConfArg| to a standard |argparse| Python parser.

All of these methods support overriding values within the solconf package directly from the command line using override strings in familiar Python syntax, for example:

.. code-block:: bash

  $ solex ./my_conf.solconf a=1 b=2

The second and third method further support mixing solconf objects with standard argparse command line options:

.. code-block:: bash

    $ my_script --opt1 \
    > --solconf-arg-1 ./my_conf1.solconf a=1 b=2 \
    > --solconf-arg-2 ./my_conf2.solconf a=1 b=2

Besides this, solconf files can also be loaded directly from Python scripts and overriden using dictionaries of Python objects::

  >>> from soleil import load_config
  >>> obj = load_config('./my_conf.solconf', overrides=[{'a':1, 'b':2}])

.. _solex:

*solex* script
-----------------------

Soleil configuration files resolve to an object or function call specified by the |as_type| member. This resolution can be invoked from the command line directly using the builtin |solex| script.

For example, the :ref:`train.solconf` example discussed in the :ref:`Getting Started` section can be invoked from the command line as follows:

.. code-block:: bash

    $ solex ./train.solconf

    100%|██████████████████████████████████████████████| 170498071/170498071 [00:15<00:00, 10742265.75it/s]
    Extracting /tmp/soleil_examples/cifar/cifar-10-python.tar.gz to /tmp/soleil_examples/cifar
    [1,  2000] loss: 2.175
    [1,  4000] loss: 1.856
    [1,  6000] loss: 1.674
    [1,  8000] loss: 1.588
    [1, 10000] loss: 1.544
    [1, 12000] loss: 1.475
    [2,  2000] loss: 1.430
    [2,  4000] loss: 1.398
    [2,  6000] loss: 1.373
    [2,  8000] loss: 1.342
    [2, 10000] loss: 1.327
    [2, 12000] loss: 1.304
    Finished Training

.. _CLI overrides:

CLI overrides
^^^^^^^^^^^^^^^

Optionally, we can override the values of any of the variables accessible from the root configuration directly through the ``solex`` invokation. For example, to change the learning rate and batch size, we could use

.. code-block:: bash

    $ solex ./train.solconf optimizer.lr=1e-4 data.dataloader.batch_size=8

The overrides must be valid Python statements that are first interpreted by the bash interpreter. So, to assign a string, we could use two sets of enclosing quotation marks, for example:

.. code-block:: bash

    $ solex ./train.solconf data.dataset.root='"~/my_root"'

Under the hood, |soleil| evaluates these string override statements using a modified Python parser that supports a subset of the Python syntax including all builtin literal values and operators.

See the :ref:`Overriding Configurations` section for other override options.

Available variables
^^^^^^^^^^^^^^^^^^^^

The |solex| script includes an experimental ``--show`` flag that skips object resolution and instead displays all the variables accessible from the root configuration:

.. code-block:: bash

    $ solex ./train.solconf --show

.. code-block::

   {
    "type:{'as_type': True, 'hidden': False, 'cast': <function <lambda> at 0x7f995ed17310>}": 'soleil_examples.cifar.train:train',
    'net': {"type:{'as_type': True, 'hidden': False, 'cast': <function <lambda> at 0x7f995ed17310>}": 'soleil_examples.cifar.model:Net'},
    'optimizer': {
        "type:{'as_type': True, 'hidden': False, 'cast': <function <lambda> at 0x7f995ed17310>}": 'torch.optim:SGD',
        'params': 'soleil.special.resolved:resolved<<resolved.parameters())>>',
        'lr': 0.001,
        'momentum': 0.9
    },
    'criterion': 'CrossEntropyLoss()',
    "data:{'hidden': True}": {
        'transform': 'Compose(\n    ToTensor()\n    Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))\n)',
        'dataset': {
            "type:{'as_type': True, 'hidden': False, 'cast': <function <lambda> at 0x7f995ed17310>}": 'torchvision.datasets:CIFAR10',
            'root': '/tmp/soleil_examples/cifar',
            'train': 'soleil.overrides.req:req<<soleil.overrides.req.req object at 0x7f98959b1c40>>',
            'download': True,
            'transform': 'Compose(\n    ToTensor()\n    Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))\n)'
        },

        ...

The output produced with this ``--show`` will be improved in later versions.

.. note:: Like |solex|-based CLI invokations, |soleil| CLIs built with the :ref:`@solex() decorator <@solex>` or using a :class:`~soleil.cli_tools.solconfarg.SolConfArg` type in a Python |argparse| parser all suport CLI overrides. Overrides with non-string values can also be specified when loading a module with |load_config| from a Python script. See :ref:`Overriding Configurations` for more information.


Running a method
^^^^^^^^^^^^^^^^^^

Sometimes, we might want to invoke a method of an object built by the |as_type| member of a solconf module. For example, given a Python package ``experiment`` containing class ``Experiment``,

.. code-block::

  # experiment/__init__.py

  class Experiment:

    param1:int
    param2:int

    def train(self):
        ...

    def eval(self):
        ...


we might be interested in calling its ``train()`` method. The |solex| script supports doing so by  means of the  ``as_run`` modifier::

  # train.solconf

  # Lets solex know to call the train method of
  # the built Experiment instance
  run:as_run = lambda exp_obj: exp_obj.train()

  # Builds an Experiment instance
  type:as_type = 'experiment.Experiment'
  param1 = 1
  param2 = 2

Invoking |solex| on this script will first instantiate the ``Experiment`` class and then invoke the ``as_run`` member on the resulting instance -- in this case, the ``as_run`` member calls the ``train`` method on the built ``Experiment`` instance.

Other solex options
^^^^^^^^^^^^^^^^^^^^^^^

The |solex| script includes other useful functionality such as (``--profile``)  the ability to profile the code run by the script, (``--pdb``) break into a debugger if an exception occurs or (``--show``) explore the configuration without resolving it.

.. code-block:: bash

    >> solex -h

    usage: solex [-h] [--profile [DO_PROFILE]] [--pdb] [--show] conf [conf ...]

    Executes a configuration file.

    positional arguments:
      conf                  The path of the configuration file to launch and, optionally, any argument overrides

    optional arguments:
      -h, --help            show this help message and exit
      --profile [DO_PROFILE]
                            Profile the code and dump the stats to a file. The flag can be followed by a filename ('solex.prof' by default)
      --pdb                 Start an interative debugging session on error
      --show                Display solconf module without resolving and exit



.. _@solex:

*@solex()* decorator
----------------------------

The |@solex| decorator can be used to convert any Python function into a CLI script that takes an object retrieved from a solconf root config as its first argument:

.. testcode:: solex

  from soleil.cli_tools import solex
  import climax as clx

  @solex()
  @clx.argument('--my-opt', default=0, type=int, help='My optional argument.')
  def foo(obj, my_opt):
      """ Optional doc string will override the default. """
      ...

  if __name__=='__main__':
     foo()

While not required, the example above makes use of the excellent |climax| module that provides a convenient |argparse| interface. One can use |@solex| in place of the `@climax.command <https://climax.readthedocs.io/en/latest/quickstart.html#getting-started>`_ decorator and subsequently decorate the function using any of the composable |climax| decorators -- in the example above we add an optional CLI argument ``--my-opt`` in this way.

One can also make the generated command part of a `command group <https://climax.readthedocs.io/en/latest/quickstart.html#building-command-groups>`__ by specifying
the climax group in the decorator as follows::

  # /usr/bin/env python
  # File './my_script'

  import climax

  @climax.group()
  def main():
      ...

  @solex(main)
  def train(obj):
      ...

  @solex(main)
  def eval(obj):
      ...

  if __name__=='__main__':
     foo()


The resulting CLI contains two subcommands that can be invoked as follows (assuming the path of the above script is *./my_script*)::

  $ ./my_script train
  $ ./my_script eval

All of the above can also be done using standard |argparse| method calls directly instead of the |climax| interface by retrieving the |ArgumentParser| object from the decorated function:

.. doctest:: solex

   >>> foo.parser
   ArgumentParser(...)



.. _argparse CLI:

*argparse* parsers
-----------------------------

Soleil supports adding described objects as Python |ArgumentParser| arguments. Such objects will be instantiated from
the description of a solconf root config. Supplying overrides is likewise supported.

Given a standard Python parser:


.. testsetup:: SolConfArg

   import argparse
   import soleil
   from pathlib import Path
   soleil_examples = Path(soleil.__file__).parent.parent / 'soleil_examples'

   import conf

   conf.fix_dict_order()

.. doctest:: SolConfArg
   :options: +NORMALIZE_WHITESPACE

   >>> import argparse
   >>> parser = argparse.ArgumentParser()


An argument whose value will be obtained by resolving a |soleil| root config can be added by setting the ``type`` keyword of that new argument to an instance of |SolConfArg|:

.. doctest:: SolConfArg
   :options: +NORMALIZE_WHITESPACE

   >>> from soleil.cli_tools import SolConfArg
   >>> parser.add_argument("new_arg", type=SolConfArg())
   ReduceAction(...)

When |SolConfArg| is initialized with no arguments, the source config will need to be specified from the CLI:

.. doctest:: SolConfArg

   >>> parser.parse_args([f"{soleil_examples}/vanilla/main.solconf"])
   Namespace(new_arg={'a': 1, 'b': 2, 'c': 3})

Alternatively, we can specify the source config in the |SolConfArg| initialization

.. doctest:: SolConfArg
   :options: +NORMALIZE_WHITESPACE

   >>> parser = argparse.ArgumentParser()
   >>> parser.add_argument("new_arg", type=SolConfArg(soleil_examples/"vanilla/main.solconf"))
   ReduceAction(...)
   >>> parser.parse_args([])
   Namespace(new_arg={'a': 1, 'b': 2, 'c': 3})

In either case, any extra CLI arguments will be interpreted as an override:

.. doctest:: SolConfArg

   >>> parser.parse_args(["a=10", "c=30"])
   Namespace(new_arg={'a': 10, 'b': 2, 'c': 30})

See the documentation of |SolConfArg| for more information.
