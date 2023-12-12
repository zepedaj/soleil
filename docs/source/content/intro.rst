Soleil: Lucid Configurations
===================================

|soleil| is a Python object configuration mechanism inspired by `Meta's Hydra <https://hydra.cc/>`_. It's main goal is to provide a Python mechanism for machine learning researchers to assemble flexible experiments in a way that is **declarative**, **inheritable**, **automatically CLI-invokable** and **intuitively overridable**.


Taming the Curse of *main.py*
-----------------------------

Machine learning experiments are often complex systems where the different components (model, optimizer, learning rate scheduler, dataset, dataloader, transformations/augmentations, and visualizations) have multiple options each defined by many different parameters.

Usually, all of these components are hard-coded into a single *main.py* file with an |argparse| command line interface that uses a global parameter namespace. Together, this *main.py*/*argparse* recipe becomes unwieldy, difficult to extend and error-prone, slowing down further research development.


|soleil|'s Approach
----------------------

|soleil|'s approach is comprised of the following:

Familiar Python Syntax
	 |soleil| configuration files (`*.solconf` files) use familiar Python syntax and can describe any installed function call, Python object, or composition thereof.
Inheritable Object Descriptions
	 The description of an object instance or function call in a configuration file takes the form of a class declaration -- object descriptions hence benefit from standard Python inheritance mechanisms.
Portable Package Organization
	 |soleil| configuration files can be organized into portable, Python-like packages. Sub-packages can be made to correspond to system components (e.g., models) that can be easily swapped by loading (see |load| and |submodule|).
Automatic, Flexible CLI
	 Any |soleil| configuration file can be run as an executable directly using the built-in |solex| tool -- a fully fledged, extensible command line utility that plays nicely with the builtin |argparse| module. Usage as a decorator (see |@solex|) or within a standard |argparse| parser is also supported (See :ref:`Automatic CLI`).
Sandboxed Overridability
	 CLI calls (through |solex| or :ref:`argparse <argparse CLI>`) involving soleil-configured objects can be modified or overriden from the command line using a subset of the Python syntax that is sandboxed through |ast| magic.


.. warning:: Soleil configurations are in effect Python programs -- only run configurations that you trust.


.. note:: The |soleil| logo and other images in this documentation were produced using a free version of |DALLE|.
