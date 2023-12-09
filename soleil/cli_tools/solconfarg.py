"""
"""

from pathlib import Path
from typing import List, Optional, Union
from uuid import uuid4
from soleil.loader.loader import load_config
from soleil.resolvers.base import resolve
import re

from soleil.resolvers.module_resolver import SolConfModule


from ._argparse_patches import ReduceAction


class SolConfArg:
    """
    Enables adding soleil configured objects as arguments in |argparse| CLIs.

    :param config_source: The path to the configuration file to load. If not specified, will be required as a CLI argument.
    :param resolve: Whether ``ArgumentParser.parse_args`` (equivalently, :meth:`__call__`) returns the resolved or unresolved object.
    :param load_kwargs: Any extra keyword arguments to pass internally to |load_config|.

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
      >>> parser.add_argument('my_obj', type=SolConfArg(soleil_examples / 'vanilla/main.solconf'))
      ReduceAction(...)
      >>> parser.parse_args([])
      Namespace(my_obj={'a': 1, 'b': 2, 'c': 3})

    .. _argparse patches note:

    .. note::

      .. rubric:: Monkey-patching of |argparse|

      |SolConfArg| monkey-patches the built-in |argparse| module in order to support having a |SolConfArg|-typed argument consume multiple command line overrides and reduce
      them to a *single* parsed element (as opposed to a list with one entry per override).

      The applied patch should not affect normal operation of |argparse| and is only applied once module :mod:`soleil.cli_tools` (or one of its member) is imported.

      The source code for theses patches is in module :mod:`soleil.cli_tools._argparse_patches`.


    .. rubric:: Under the hood

    Using a |SolConfArg| instance as the type of a parser argument implicitly sets the default value of the ``nargs`` and ``action`` arguments::

      parser = ArgumentParser()
      parser.add_argument(
        ...
        type=SolConfArg(...),
        action=<defaults to ReduceAction()>,
        nargs=<defaults to '+' or '*'>,
        ...
      )
      parser.parse_args([...])

    The ``action`` keyword is set to an instance of ``ReduceAction()`` that is responsible for gathering all the CLI arguments corresponding to the ``SolConfArg()`` parser
    entry as overrides and  resolving the described object with these overrides included by means of a call to :meth:`SolConfArg.__call__`.

    Accordingly, the object returned for the argument added in the code above can also be obtained as follows::

      sc = SolConfArg(...)
      sc([...])

    .. note:: For conciseness, we use the above syntax in examples below.


    .. _number of consumed cli arguments:

    .. rubric:: Number of consumed CLI arguments

    If  ``config_source`` is not provided at |SolConfArg| initialization, the first CLI argument will be used in its place. Accordingly CLI arguments of type |SolConfArg| will by default consume

      * one-or-more CLI arguments when ``config_source`` is not provided, or
      * zero-or-more CLI arguments when ``config_source`` is provided.

    Any extra CLI arguments besides ``config_source`` are treated as :ref:`CLI overrides`.

    This behavior is implemented by internally setting the default value of keyword argument ``nargs`` using

     * ``nargs='+'`` or ``nargs='*'``, respectively,

    in the :meth:`argparse.ArgumentParser.add_argument` call. Users can change this behavior, e.g., by using

      * ``nargs=1`` or ``nargs=0``, respectively,

    in effect disabling :ref:`CLI overrides`.

    .. note::

      An |argparse| argument of type |SolConfArg| with the default ``nargs='+'`` or ``nargs='*'`` will consume an unbounded number of CLI arguments. Such arguments must either be the last non-optional argument added to the :class:`ArgumentParser` object, or an optional argument.

    .. note::

      Even when :class:`SolConfArg` is instantiated with a ``config_source`` argument, the value of ``config_source`` can be overriden from the command line using a :ref:`source clobber <source clobber>` override.

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

    """

    def __init__(
        self,
        config_source: Optional[Union[Path, str]] = None,
        resolve=True,
        **load_kwargs,
    ):
        """ """

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
        Resolves the argument, applying all input overrides.
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
