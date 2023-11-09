from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, List, Union
import ast
from uuid import uuid4
from soleil.loader.override import Handled, Override
from soleil._utils import PathSpec, Unassigned
import importlib.util
import importlib.machinery
import importlib._bootstrap
import sys
from . import pre_processor

from soleil.resolvers.module_resolver import ModuleResolver, SolConfModule
from soleil.resolvers.base import resolve as call_resolve

DEFAULT_EXTENSION = ".solconf"
DEFAULT_PACKAGE_NAME = "solconf"


def load_config(conf_path: PathSpec, package_name=DEFAULT_PACKAGE_NAME, resolve=True):
    """
    Creates a new instance of the solconf module at the specfied path.

    :param conf_path: A file with solconf extension. The package will implicitly be assigned to the directory of this file.
    :param package_name: [``'solconf'``] The package name.
    :param resolve: [``True``] Whether the resolve the module.
    """

    # Check path is a *.solconf file
    conf_path = Path(conf_path)
    if conf_path.suffix != DEFAULT_EXTENSION or not conf_path.is_file():
        raise ValueError(f"Expected a `*.solconf` file but received `{conf_path}`")

    #
    package_name = GLOBAL_LOADER.init_package(conf_path.parent)
    module_name = f"{package_name}.{conf_path.stem}"

    return GLOBAL_LOADER.load(module_name, resolve=resolve)


class ConfigLoader:
    """
    Loads solconf packages and applies CLI overrides.
    """

    overrides: List[Override]
    modules: Dict[str, SolConfModule]
    """ Contains previously-loaded modules or package paths """
    package_roots: Dict[str, Path]
    """ Contains the roots of solconf pacakges """

    def __init__(self):
        """See the documentation for :func:`load_config`."""
        self.modules = {}
        self.package_roots = {}

    def init_package(self, path: Union[str, Path], name: Optional[str] = None):
        """
        Initializes a solconf package at the specified path and with the given name (random name by default).
        """
        name = name or uuid4().hex
        if name in self.package_roots:
            raise ValueError(
                f"Attempted to reinitialize existings solconf package `{name}`"
            )
        self.package_roots[name] = Path(path).resolve(strict=True)
        return name

    def get_sub_module_path(self, abs_module_name, check_exists=True):
        """
        Maps an absolute module name to a file path.
        """
        components = abs_module_name.split(".", -1)
        package_name = components[0]
        package_root = self.package_roots[package_name]
        sub_packages = components[:-1]
        module_name = components[-1]
        module_path = package_root.joinpath(
            *sub_packages[1:], module_name + DEFAULT_EXTENSION
        )

        # Check that the module path exists
        if check_exists and not module_path.is_file():
            raise ValueError(
                f"No solconf module  `{abs_module_name}` (module path `{module_path.absolute()})`."
            )

        return module_path

    def load(self, abs_module_name, resolve=True, promoted=True):
        """
        :param module_name: The absolute module name (e.g., ``package_name.sub_module_1.sub_module_2``)
        :param resolve: Return the model's resolved value if ``True``, otherwise the module itself.
        :param promoted: Whehter to return the promoted member of teh full module. Only has an effect when ``resolve=False``.
        :param reqs: The values for the required module members.
        """

        sub_module_path = self.get_sub_module_path(abs_module_name)

        # Create the module
        module = self._build_solconf_module(sub_module_path, abs_module_name)

        # Exec the module code
        self._exec_solconf_module(module)

        # Get the promoted member
        if (
            not resolve
            and promoted
            and (mod_rslvr := ModuleResolver(module)).promoted is not Unassigned
        ):
            out = mod_rslvr.promoted
        else:
            out = module

        # Resolve the output
        if resolve:
            return call_resolve(out)
        else:
            return out

    def _build_solconf_module(self, module_path: PathSpec, abs_module_name: str):
        """
        Returns a previously-built or newly-built module.

        :param path: The path to the file.
        :param abs_module_name: [Default is ``'solconf.<module_path stem>'``] The name of the module in python. A package name can be pre-pended to the module-name with a '.' separator. After calling this function, the module can be imported from any other module using ``import <abs_module_name>``.
        """

        module_path = Path(module_path)

        if abs_module_name in self.modules:
            # The conf module was previously loaded.
            module = self.modules[abs_module_name]
            if (loaded_path := Path(module.__file__)) != module_path:
                # The previous load path differs
                raise ValueError(
                    f"The specified solconf module `{abs_module_name}` was previously "
                    f"loaded from a path `{loaded_path}` that is not the requested path `{requested_path}`."
                )
            if ModuleResolver(module)._get_required_member_names():
                # The module has required vars that need to be injected
                raise ValueError(
                    f"Solconf modules with required members can only be loaded once."
                )
        else:
            # Instantiate the solconf module
            module_path = Path(module_path)
            module = SolConfModule(abs_module_name)
            module.init_as_module(abs_module_name, module_path)
            self.modules[abs_module_name] = module

        return module

    def _exec_solconf_module(self, module: SolConfModule):
        with open(module.__file__, "rt") as fo:
            code = fo.read()
        tree = ast.parse(code)

        # Apply the pre-processor
        spp = pre_processor.SoleilPreProcessor(overrides=[])
        tree = spp.visit(tree)

        # Execute the module
        out = {}
        exec(
            compile(tree, filename=str(module.__file__), mode="exec"),
            dict(vars(module)),
            out,
        )
        [setattr(module, key, val) for key, val in out.items()]

        # Append the imported ignores
        module.__soleil_default_hidden_members__.update(spp.imported_names)


GLOBAL_LOADER = ConfigLoader()
