from typing import Callable
from rich import print
import climax as clx
from soleil.solconf.cli_tools.solconfarg import SolConfArg
from .helpers import import_extra_modules


class _NotProvided:
    pass


def solex(
    group: Callable = clx, *, _fxn: Callable = _NotProvided, do_post_proc: bool = True
) -> Callable:
    """
    Decorator that builds a CLI command similar to the :ref:`solex script <solex script>` and applies the wrapped callable, if any, to the object deserialized from the configuration file.

    The returned command exposes a ``parser`` attribute of type |argparse.ArgumentParser| that can be used to add extra CLI arguments that are passed to the wrapped callable. Depending on the specifications of the ``conf`` argument of type |SolConfArg|, these extra arguments might need to be optional |argparse| arguments (see :ref:`Number of consumed CLI arguments` in the |SolConfArg| documentation).

    :param group: Pass in a climax group to make the solex call a sub-command.
    :param do_post_proc: Whether to apply the post-processor before passing in the deserializaed configuration object to the wrapped callable.

    .. rubric:: Example usage

    The function can be used as a decorator to define python scripts that execute a function on the object loaded from the configuration file:


    .. testcode:: solex

      import soleil as sl

      @sl.solex()
      @sl.argument('--my-opt', default=0, type=int, help='My optional argument.')
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

      usage: ... [-h] [--modules [MODULES [MODULES ...]]] [--print {final,resolved,tree,tree-no-modifs}]
             [--my-opt MY_OPT] conf [conf ...]

      Optional doc string will override the default.

      positional arguments:
        conf                  The path of the configuration file to launch and, optionally, any argument
                              overrides.

      optional arguments:
        -h, --help            show this help message and exit
        --modules [MODULES [MODULES ...]]
                              The modules to load before execution - can be used to register soleil
                              parser context variables or xerializable handlers. Any module specified as
                              part of a list `modules` in a `.solex` YAML file at the same level as the
                              configuration file will also be loaded.
        --print {final,resolved,tree,tree-no-modifs}
                              Prints ('final') the final value, after the post-processor is applied,
                              ('resolved') the resolved contents before applying the post-processor or
                              ('tree') the node tree, optionally ('tree-no-modifs') before applying
                              modifications.
        --my-opt MY_OPT       My optional argument.


    Note that the option also supports adding an extra arguments ``--my-opt`` that is also passed to the test function ``foo`` as argument ``my_opt``.

    .. note::

        Soleil CLIs are based on `climax <https://climax.readthedocs.io/en/latest/quickstart.html>`_ and can be combined with any climax construct. Both ``soleil.argument`` and ``soleil.group`` are aliases to ``climax.argument`` and ``climax.group``.


    .. rubric:: Usage within a command group

    The ``@solex`` decorator can also be used to define climax sub-commands.

    .. testcode:: solex

      import soleil as sl

      @sl.group()
      def my_command_group(): pass

      @my_command_group.command()
      def bar(): pass

      @sl.solex(my_command_group)
      @sl.argument('--my_opt', default=0, type=int, help='My optional argument.')
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
        return lambda _fxn1: solex(group=group, _fxn=_fxn1, do_post_proc=do_post_proc)

    # @clx.command() decorator delayed to support changing the __doc__ string -- see below.
    @clx.argument(
        "conf",
        type=SolConfArg(resolve=False),
        help="The path of the configuration file to launch and, optionally, "
        "any argument overrides.",
    )
    @clx.argument(
        "--print",
        action="store_true",
        dest="do_print",
        help="Prints the resolved contenst of the config file before applying the post-processor or executing.",
    )
    @clx.argument(
        "--modules",
        nargs="*",
        default=None,
        help="The modules to load before execution - can be used to register soleil parser context variables or xerializable handlers. Any module specified as part of a list `modules` in a `.solex` YAML file at the same level as the configuration file will also be loaded.",
    )
    def solex_run(conf, do_print, modules, **kwargs):
        """
        Executes a configuration file and/or, optionally, prints its contents at various points of the parsing process.

        If a `.solex` file is found next to the specified configuration file, it is intepreted as a YAML file and any extra modules in root-level list `modules` are appended to the contents of the CLI-specified modules to load.
        """

        # Get the config source path
        config_source, _ = conf.get_config_source()

        # Load any extra modules specified in the CLI or in the .solex file.
        import_extra_modules(modules, config_source)

        # Apply overrides, get SolConf object.
        sc = conf.apply_overrides()

        #
        sc.modify_tree()
        if do_post_proc:
            # Executes the post-processor, and hence any commands.
            out = sc()
        else:
            out = sc.root()

        if do_print:
            print(out)
        else:
            _fxn(out, **kwargs)

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
