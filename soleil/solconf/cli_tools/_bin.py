from rich import print
import yaml
from pathlib import Path
from importlib import import_module
import climax as clx
from soleil.solconf.cli_tools import SolConfArg


def load_dot_solex(config_source, modules):
    """
    Loads any extra arguments specified in a ``.solex`` file at the same level as the ``config_source`` file.
    """
    if (dot_solex := Path(config_source).parent / '.solex').is_file():
        with open(dot_solex, 'rt') as fo:
            yaml_str = fo.read()
        params = yaml.safe_load(yaml_str)
        modules = list((modules or [])) + params['modules']

    return modules


@clx.command()
@clx.argument('conf', type=SolConfArg(resolve=False),
              help='The path of the configuration file to launch and, optionally, any argument overrides.')
@clx.argument(
    '--print', choices=['final', 'resolved', 'tree', 'tree-no-modifs'],
    dest='print_what', default=None,
    help="Prints ('final') the final value, after the post-processor is applied, ('resolved') the resolved  contents before applying the post-processor or ('tree') the node tree, optionally ('tree-no-modifs') before applying modifications.")
@clx.argument(
    '--modules', nargs='*',
    help='The modules to load before execution - can be used to register soleil parser context variables or xerializable handlers. Any module specified as part of a list `modules` in a `.solex` YAML file at the same level as the configuration file will also be loaded.')
def solex(conf, print_what, modules):
    """
    Executes a configuration file and/or, optionally, prints its contents at various points of the parsing process.

    If a `.solex` file is found next to the specified configuration file, it is intepreted as a YAML file and any extra modules in root-level list `modules` are appended to the contents of the CLI-specified modules to load.
    """

    # Load any extra config values from .solex file.
    modules = load_dot_solex(conf.solconfarg_config_source, modules)

    for _mdl in modules:
        import_module(_mdl)

    if print_what == 'resolved':
        conf.modify_tree()
        print(conf.root())
    elif print_what == 'tree':
        conf.modify_tree()
        conf.print_tree()
    elif print_what == 'tree-no-modifs':
        conf.print_tree()
    elif print_what in [None, 'final']:
        # Executes  the post-processor, and hence any commands.
        conf.modify_tree()
        out = conf()
        if print_what == 'final':
            print(out)
    else:
        raise Exception('Unexpected case.')
