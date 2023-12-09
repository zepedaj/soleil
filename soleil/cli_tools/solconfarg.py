"""
"""

from typing import List, Optional
from uuid import uuid4
from soleil.loader.loader import load_config
from soleil.resolvers.base import resolve
import re

from soleil.resolvers.module_resolver import SolConfModule


from ._argparse_patches import ReduceAction


class SolConfArg:
    """
    Enables adding soleil configured objects as arguments in |argparse| CLIs.

    Instances of this object can be passed as a value for the ``type`` keyword argument when calling :meth:`argparse.ArgumentParser.add_argument` (see the  |argparse| documentation).

    Assuming no :ref:`overrides <CLI overrides>` are specified, doing so will set the parsed value of that argument to the resolved object loaded from the ``config_source`` initialization argument:

    .. testsetup:: SolConfArg

      from pathlib import Path
      from soleil.cli_tools import SolConfArg
      from rich import print

      from soleil.cli_tools import solconfarg
      soleil_examples = Path(solconfarg.__file__).parent.parent.parent / 'soleil_examples'

      from collections import OrderedDict

      def sort_dicts(d):
          if isinstance(d, dict):
              return dict((k, sort_dicts(v)) for k,v in sorted(d.items()))
          else:
              return d

      # Patch SolConfArg.__call__

      global _orig_sca_call
      _orig_sca_call = SolConfArg.__call__

      def __call__(self, *args, **kwargs):
          out = sort_dicts(_orig_sca_call(self, *args, **kwargs))
          return out

      SolConfArg.__call__ = __call__

      # Patch parser
      from argparse import ArgumentParser

      global _orig_parse_args
      _orig_parse_args = ArgumentParser.parse_args

      def parse_args(self, *args, **kwargs):
          out = _orig_parse_args(self, *args, **kwargs)
          for key in vars(out):
              setattr(out, key, sort_dicts(getattr(out,key)))

          return out



      ArgumentParser.parse_args = parse_args

    .. doctest:: SolConfArg

      >>> from argparse import ArgumentParser
      >>> from soleil.cli_tools import SolConfArg

      >>> parser = ArgumentParser()
      >>> parser.add_argument('sc', type=SolConfArg(soleil_examples / 'vanilla/main.solconf'))
      ReduceAction(...)
      >>> parser.parse_args([])
      Namespace(sc={'a': 1, 'b': 2, 'c': 3})

    .. _argparse patches note:

    .. note::

      .. rubric:: Patching of Python builtin module |argparse|

      |SolConfArg| integration with the Python builtin module |argparse| requires that patches be applied to the :class:`ArgumentParser` class of that module. The patches should not affect normal operation of that module.

      Patches are only applied once :mod:`soleil.cli_tools` (or a member) is imported and hence all :class:`ArgumentParser` instances that will take |SolConfArg| argument types must be instantiated after importing :mod:`soleil.cli_tools`.

      See the source code in :mod:`soleil.cli_tools._argparse_patches` for the actual patches.

    .. _number of consumed cli arguments:

    .. rubric:: Number of consumed CLI arguments

    If  ``config_source`` is not provided at |SolConfArg| initialization, the first CLI argument will be used in its place. Accordingly CLI arguments of type |SolConfArg| will by default consume

      * one-or-more CLI arguments when ``config_source`` is not provided, or
      * zero-or-more CLI arguments when ``config_source`` is provided.

    Any extra CLI arguments besides ``config_source`` are treated as :ref:`CLI overrides`.

    This behavior is implemented by internally setting the default keyword arguments

     * ``nargs='+'`` or ``nargs='*'``, respectively,

    in the :meth:`argparse.ArgumentParser.add_argument` call. Users can change this behavior, e.g., by using

      * ``nargs=1`` or ``nargs=0``, respectively,

    in effect disabling :ref:`CLI overrides`.

    .. note::

      An |argparse| argument of type |SolConfArg| with the default ``nargs='+'`` or ``nargs='*'`` will consume an unbounded number of CLI arguments. Such arguments must either be the last non-optional argument added to the :class:`ArgumentParser` object, or an optional argument.

    .. note::

      Even when :class:`SolConfArg` is instantiated with a ``config_source`` argument, the value of ``config_source`` can be overriden from the command line using a :ref:`source clobber <source clobber>` override.

    .. rubric:: CLI overrides

    Extra CLI arguments passed to an |argparse| argument of type |SolConfArg| specify overrides that change the values in the loaded resolvable. Override specifiers can be of three types:

        * **Value assignment (=)**: Valid if the target is a :class:`~soleil.solconf.nodes.ParsedNode`, in which case the assignment replaces the :attr:`~soleil.solconf.nodes.ParsedNode.raw_value` of the :class:`~soleil.solconf.nodes.ParsedNode` with the new value.
        * **Clobber assignment (*=)**: Create a new node (or node sub-tree) from the provided raw content. The target node, if any, is discarded, and the new node added.
        * **Source clobber (**=)**: Sets or replaces the ``config_source`` argument of the ``SolConfArg`` object. See :ref:`below <source clobber>`.

    """

    def __init__(self, config_source: str = None, resolve=True, **load_kwargs):
        """

        :param config_source: The path to the configuration file to load.
        :param resolve: Whether :meth:`__call__` returns the resolved content, or the un-modified and un-resolved :class:`SolConfArg` object (after applying any overrides).

        .. doctest:: SolConfArg

          # Option 1: Path must be provided with argparse arguments
          >>> sca1 = SolConfArg()
          >>> sca1([soleil_examples/'vanilla/main.solconf', "typing_a=c++", "typing_b=c++"])
          {'a': 1, 'b': 2, 'c': 3}

          # Option 2: Path provided with argument definition
          >>> sca2 = SolConfArg(soleil_examples/'vanilla/main.solconf')
          >>> sca2(["a=10", "c=30"])
          ...'a': 10...


        .. _source clobber:

        .. rubric:: Source clobber

        In the case where a path is specified in the initializer, it can still be overriden using a  **source clobber** override:

        .. doctest:: SolConfArg

          # Source clobber assignment must be the first argument in the overrides list

          >>> sca2 = SolConfArg(soleil_examples/'vanilla/main.solconf')
          >>> sca2([f"**={soleil_examples/'vanilla/nested.solconf'}"])
          {'letters': {'a': 1, 'b': 2, 'c': 3}}

        Note that the source clobber override must be the first item in the overrides list.


        .. rubric:: Deeper overrides

        The target of an override provided to the left of the override assignment operator can consist of any valid :ref:`variable name path <variable name paths>`:

        .. doctest:: SolConfArg
           :options: +NORMALIZE_WHITESPACE

           >>> sca = SolConfArg(soleil_examples/'vanilla/nested.solconf')
           >>> sca() ##
           {'letters': {'a': 1, 'b': 2, 'c': 3}}
           >>> sca(['letters.b=20'])
           {'letters': {'a': 1, 'b': 20, 'c': 3}}


        .. rubric:: Usage with ``argparse`` parsers

        .. doctest:: SolConfArg

          >>> import argparse
          >>> import soleil.cli_tools # *** Must be done before ArgumentParser instantiation ***
          >>> parser = argparse.ArgumentParser()

          # Setting type=SolConfArg() implicitly sets nargs='+' and action=ReduceAction by default.
          >>> parser.add_argument('arg1', type=SolConfArg())
          ReduceAction(option_strings=[], dest='arg1', nargs='+', ... type=<...SolConfArg...>, ...)

          # Path required since SolConfArg initialized with no arguments!
          >>> parser.parse_args([])
          Traceback (most recent call last):
              ...
          SystemExit: 2

          # With no overrides
          >>> parser.parse_args([f"{soleil_examples}/vanilla/main.solconf"])
          Namespace(arg1={'a': 1, 'b': 2, 'c': 3})

          # With overrides
          >>> parser.parse_args([f"{soleil_examples}/vanilla/main.solconf", "a=10", "c=30"])
          Namespace(arg1={'a': 10, 'b': 2, 'c': 30})

        .. note::

          *Help! I'm getting the error message* ``AttributeError: 'str' object has no attribute 'pop'`` *!*

          There are two possible reasons for this error:

            #. The :class:`ArgumentParser` class from the |argparse| module was instantiated before :mod:`soleil.solconf.cli_tools` was imported. See the :ref:`related note <argparse patches note>` on |argparse| patches.
            #. Using :class:`SolConfArg` argument instances as the ``type`` keyword argument  in a ``ArgumentParser.add_argument`` call requires that the ``action=ReduceAction``  keyword-value pair be used as well. This keyword pair is used by default when ``type`` is a :class:`SolConfArg` instance. Have you explicitly set the ``action`` keyword argument to a different value?

        """

        self._config_source = config_source
        self._resolve = resolve
        self.load_kwargs = load_kwargs
        self.overrides = None

    @property
    def DFLT_ARGPARSE_KWARGS(self):
        """
        Sets the default ``argparser.add_argument`` keyword argument values to use when this instance is used as the ``type`` keyword argument.
        """
        return {
            "nargs": "+" if self._config_source is None else "*",
            "action": ReduceAction,
        }

    def __call__(self, overrides: Optional[List[str]] = None):
        """
        If the object was initialized without specifying a ``config_source``, then the first entry of ``overrides`` must contain it.

        .. rubric:: Workflow:

        1) Load the configuration file specified by ``config_source`` to create a :class:`SolConf` object. Do not apply modifiers during :class:`SolConf` initialization..
        2) For each override:

          1) For consistency with :class:`SolConf.load` any input value is first loaded using ``yaml.safe_load`` -- this does some interpretation. For example strings that represent integers, booleans or null are converted to an integer, boolean and ``None``, respectively. The resulting value is the **raw content**.
          2) Apply all modifiers of the path implicit in the reference string (except for the last component) -- this is done implicitly with :meth:`Node.__getitem__`. Doing so enables e..g, modifying nodes that are load targets. Because of this application of modifiers, the order in which overrides are provided is important.
          3) Assign the override value depending on the :ref:`override type <CLI overrides>`.

        """

        self.overrides = list(overrides or [])
        return self.build_sol_conf()

    def get_config_source(self):
        """
        Returns the config source path, which will depend on whether a config source was specified explicitly at initialization or not, and whether a source clobber override was specified.
        """
        overrides = list(self.overrides)

        if overrides and (
            root_clobber := re.match(r"^\*\*\=(?P<path>.*$)", overrides[0])
        ):
            # Check for source clobber
            overrides.pop(0)
            config_source = root_clobber["path"]
        elif self._config_source is None:
            # If config file not previously defined, get from overrides
            config_source = overrides.pop(0)
        else:
            config_source = self._config_source

        return config_source, overrides

    def build_sol_conf(self) -> SolConfModule:
        # Get cli args
        config_source, overrides = self.get_config_source()

        # Load module -- add a random package name
        loaded = load_config(
            config_source,
            resolve=False,
            overrides=overrides,
            **{"package_name": uuid4().hex, **self.load_kwargs},
        )

        if self._resolve:
            return resolve(loaded)
        else:
            return loaded
