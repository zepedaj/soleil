from contextlib import nullcontext
from typing import Callable
import traceback, sys

try:
    import ipdb as pdb
except ModuleNotFoundError:
    import pdb

import cProfile
from jztools.rentemp import RenTempFile

from rich import print
import climax as clx
from soleil.cli_tools import SolConfArg
from soleil.resolvers.module_resolver import ModuleResolver
from soleil import resolve as call_resolve


class _NotProvided:
    pass


def solex(
    group: Callable = clx, *, _fxn: Callable = _NotProvided, **solconfarg_kwargs
) -> Callable:
    """
    Decorator that builds a CLI command similar to the |solex| script and applies the wrapped callable, if any, to the object resolved from the configuration file.

    The returned command exposes a ``parser`` attribute of type `argparse.ArgumentParser <https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser>`_ that can be used
    to add extra CLI arguments that are passed to the wrapped callable. Depending on the specifications of the ``conf`` argument of type :class:`~soleil.cli_tools.solconfarg.SolConfArg`,
    these extra arguments might need to be optional `argparse <https://docs.python.org/3/library/argparse.html>`_ arguments (see :ref:`Number of consumed CLI arguments` in the
    :class:`~soleil.cli_tools.solconfarg.SolConfArg` documentation).

    :param group: Pass in a climax group to make the solex call a sub-command.


    .. rubric:: Example usage

    The function can be used as a decorator to define python scripts that execute a function on the object loaded from the configuration file:


    .. testcode:: solex

      from soleil.cli_tools import solex
      import climax as clx

      @solex()
      @clx.argument('--my-opt', default=0, type=int, help='My optional argument.')
      def foo(obj, my_opt):
          \"\"\" Optional doc string will override the default. \"\"\"
          ...

      if __name__=='__main__':
         foo()

    .. testcode:: solex
      :hide:

      foo.parser.print_help()

    Running the above script with the ``-h`` option displays the following help message:

    .. testoutput:: solex
      :options: +NORMALIZE_WHITESPACE


      usage: sphinx-build [-h] [--profile [DO_PROFILE]] [--pdb] [--show] [--my-opt MY_OPT] conf [conf ...]

      Optional doc string will override the default.

      positional arguments:
        conf                  The path of the configuration file to launch and, optionally, any argument overrides

      optional arguments:
        -h, --help            show this help message and exit
        --profile [DO_PROFILE]
                              Profile the code and dump the stats to a file. The flag can be followed by a filename ('solex.prof' by default)
        --pdb                 Start an interative debugging session on error
        --show                Display solconf module without resolving and exit
        --my-opt MY_OPT       My optional argument.

    Note that the option also supports adding an extra arguments ``--my-opt`` that is also passed to the test function ``foo`` as argument ``my_opt``.

    .. note::

        Soleil CLIs are based on `climax <https://climax.readthedocs.io/en/latest/quickstart.html>`_ and can be combined with any climax construct. Both ``soleil.argument`` and ``soleil.group`` are aliases to ``climax.argument`` and ``climax.group``.


    .. rubric:: Usage within a command group

    The ``@solex`` decorator can also be used to define climax sub-commands.

    .. testcode:: solex

      from soleil.cli_tools import solex
      import climax as clx

      @clx.group()
      def my_command_group(): pass

      @my_command_group.command()
      def bar(): pass

      @solex(my_command_group)
      @clx.argument('--my_opt', default=0, type=int, help='My optional argument.')
      def foo(obj, my_opt):
          \"\"\" Optional doc string will override the default. \"\"\"
          ...

      if __name__=='__main__':
         my_command_group()

    .. testcode:: solex
      :hide:

      my_command_group.parser.print_help()

    Running the above script with the ``-h`` option displays the following help message:

    .. testoutput:: solex
      :options: +NORMALIZE_WHITESPACE

        usage: ... [-h] {bar,foo} ...

        positional arguments:
          {bar,foo}
            bar
            foo       Optional doc string will override the default.

        optional arguments:
          -h, --help  show this help message and exit

    """

    if _fxn is _NotProvided:
        return lambda _fxn1: solex(group=group, _fxn=_fxn1, **solconfarg_kwargs)

    #
    do_resolve = solconfarg_kwargs.pop("resolve", True)

    # @clx.command() decorator delayed to support changing the __doc__ string -- see below.
    @clx.argument(
        "conf",
        type=SolConfArg(resolve=False, **solconfarg_kwargs),
        help="The path of the configuration file to launch and, optionally, "
        "any argument overrides",
    )
    @clx.argument(
        "--show",
        action="store_true",
        help="Display solconf module without resolving and exit",
    )
    @clx.argument(
        "--pdb",
        dest="do_pdb",
        action="store_true",
        help="Start an interative debugging session on error",
    )
    @clx.argument(
        "--profile",
        dest="do_profile",
        default=None,
        const=(const := "solex.prof"),
        nargs="?",
        help=f"Profile the code and dump the stats to a file. The flag can be followed by a filename ('{const}' by default)",
    )
    def solex_run(conf, show, do_pdb, do_profile, **kwargs):
        # The function `_fxn` being run can optionally have arguments decorated with climax.
        # Any such argument is passed in `**kwargs`.
        """
        Executes a configuration file.
        """
        with cProfile.Profile() if do_profile else nullcontext() as pr, RenTempFile(
            do_profile, partial=True, overwrite=True
        ) if do_profile else nullcontext() as profile_temp_file:
            try:
                if show:
                    print(ModuleResolver(conf).displayable())
                else:
                    _fxn(call_resolve(conf) if do_resolve else conf, **kwargs)
            except KeyboardInterrupt:
                pass
            except Exception:
                if not do_pdb:
                    raise
                else:
                    extype, value, tb = sys.exc_info()
                    traceback.print_exc()
                    pdb.post_mortem(tb)

            if pr and profile_temp_file:
                pr.dump_stats(profile_temp_file.name)

    # Change the doc string.
    if _fxn.__doc__ is not None:
        solex_run.__doc__ = _fxn.__doc__

    # Apply any extra arguments
    for args, kwargs in getattr(_fxn, "_arguments", []):
        solex_run = clx.argument(*args, **kwargs)(solex_run)

    # Delay the @clx.command() decorator to support changing
    # the doc string.
    solex_run.__name__ = _fxn.__name__
    solex_run = group.command()(solex_run)

    return solex_run
