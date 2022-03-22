from rich import print
import yaml
from pathlib import Path
from importlib import import_module
import climax as clx
from soleil.solconf.cli_tools import SolConfArg


def load_dot_solex(config_source):
    """
    Loads any extra arguments specified in a ``.solex`` file at the same level as the ``config_source`` file.
    """
    if (dot_solex := Path(config_source).parent / '.solex').is_file():
        with open(dot_solex, 'rt') as fo:
            yaml_str = fo.read()
        params = yaml.safe_load(yaml_str)

    return params


def solex(fxn=None):
    """
    Decorator that builds a CLI command similar to the :ref:`solex script <solex script>` and applies the callable ``fxn``, if any, to the object deserialized from the configuration file.

    The returned command exposes a ``parser`` attribute of type |argparse.ArgumentParser| that can be used to add extra CLI arguments that are passed to the ``fxn`` callable. Depending on the specifications of the ``conf`` argument of type |SolConfArg|, these extra arguments might need to be optional |argparse| arguments (see :ref:`Number of consumed CLI arguments` in the |SolConfArg| documentation).

    .. rubric:: Example usage

    The function can be used as a decorator to define python scripts that execute a function on the object loaded from the configuration file:

    .. testcode:: solex

      from soleil.solconf.cli_tools import solex
      @solex
      def foo(obj, my_opt):
          \"\"\" Optional doc string will override the default. \"\"\"
          ...

      # Add any extra arguments
      foo.parser.add_argument('--my_opt', default=0, type=int, help='My optional argument.')

      if __name__=='__main__':
         foo()



    .. testcode:: solex
      :hide:

      foo.parser.print_help()

    Running the above script with the ``-h`` option displays the following help message:

    .. testoutput:: solex
      :options: +NORMALIZE_WHITESPACE

      usage: ... [-h] [--modules [MODULES [MODULES ...]]] [--print {final,resolved,tree,tree-no-modifs}] 
             [--my_opt MY_OPT] conf [conf ...]

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
        --my_opt MY_OPT       My optional argument.
    """

    # @clx.command() decorator delayed to support changing the __doc__ string -- see below.
    @clx.argument(
        'conf', type=SolConfArg(resolve=False),
        help='The path of the configuration file to launch and, optionally, '
        'any argument overrides.')
    @clx.argument(
        '--print', choices=['final', 'resolved', 'tree', 'tree-no-modifs'],
        dest='print_what', default=None,
        help="Prints ('final') the final value, after the post-processor is applied, ('resolved') the resolved  contents before applying the post-processor or ('tree') the node tree, optionally ('tree-no-modifs') before applying modifications.")
    @clx.argument(
        '--modules', nargs='*', default=[],
        help='The modules to load before execution - can be used to register soleil parser context variables or xerializable handlers. Any module specified as part of a list `modules` in a `.solex` YAML file at the same level as the configuration file will also be loaded.')
    def solex_run(conf, print_what, modules, **kwargs):
        """
        Executes a configuration file and/or, optionally, prints its contents at various points of the parsing process.

        If a `.solex` file is found next to the specified configuration file, it is intepreted as a YAML file and any extra modules in root-level list `modules` are appended to the contents of the CLI-specified modules to load.
        """

        # Get the config source path
        config_source, _ = conf.get_config_source()

        # Load any extra modules specified in the CLI or in the .solex file.
        modules = modules + load_dot_solex(config_source).get('modules', [])
        for _mdl in modules:
            import_module(_mdl)

        # Apply overrides, get SolConf object.
        sc = conf.apply_overrides()

        #
        if print_what == 'tree-no-modifs':
            sc.print_tree()
        elif print_what == 'tree':
            sc.modify_tree()
            sc.print_tree()
        elif print_what == 'resolved':
            sc.modify_tree()
            # Calling the root resolver skips the post-processor.
            print(sc.root())
        elif print_what in [None, 'final']:
            sc.modify_tree()
            # Executes the post-processor, and hence any commands.
            out = sc()
            # If a callable was specified, apply it to the resolved+post-processed output.
            if fxn:
                out = fxn(out, **kwargs)
            if print_what == 'final':
                print(out)
        else:
            raise Exception('Unexpected case.')

    # Change the doc string.
    if fxn and fxn.__doc__ is not None:
        solex_run.__doc__ = fxn.__doc__

    # Delay the @clx.command() decorator to support changing
    # the doc string.
    solex_run = clx.command()(solex_run)

    return solex_run
