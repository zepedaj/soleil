Soleil - Lucid configurations
===================================

Soleil is a Python object configuration mechanism inspired by Meta's `Hydra <https://hydra.cc/>`_.

.. rubric:: Researcher Block: Taming the Curse of *main.py*

Soleil's main goal is to provide a Python mechanism to assemble *complex, extensible systems* in a *declarative, configurable manner* that is *automatically CLI-overridable* with *minimal coding overhead*.

An example of such a system is a machine learning training system, where the different components (model, optimizer, dataset, dataloader, augmentations, and visualizations) have multiple options each defined by many different parameters.

Usually, all of these components are hard-coded into a single `main.py <https://github.com/pytorch/examples/blob/main/word_language_model/main.py>`_ file with an |argparse| CLI interface with global parameter namespace that together become unwieldy and error-prone when more and more combinations are explored, slowing down further research development.


.. rubric:: The Soleil Way

Soleil's answer to the above problems is comprised of the following:

* **Familiar Python Syntax:** Soleil configuration files (``*.solconf`` files) use familiar Python syntax and can describe any installed function call, Python object, or composition thereof.
* **Inheritable Object Descriptions:** The description of an object instance in a configuration file takes the form of a class declaration -- object descriptions hence benefit from standard Python inheritance mechanisms.
* **Portable Package Organization:** Soleil configuration files can be organized into portable, Python-like packages.
* **Automatic, Flexible CLI:** Any soleil configuration file can be run as an executable directly using the built-in :mod:`~soleil.scripts.solex` tool -- a fully fledged, extensible command line utility that plays nicely with the builtin :mod:`argparse` module. Usage as a decorator (see :func:`~soleil.cli_tools.solex.solex`) or within a standard :mod:`argparse` parser is also supported.
* **Sandboxed Overridability:** CLI calls (through |solex| or |argparse|) involving soleil configured objects can be modified or overriden from the command line using a subset of the Python syntax that is sandboxed through |ast| magic.
