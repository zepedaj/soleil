from pathlib import Path
from typing import Dict, Optional, List, Union
import ast
from uuid import uuid4
from soleil._utils import PathSpec, Unassigned

from soleil.overrides.overrides import OverrideSpec, eval_overrides
from soleil.overrides.variable_path import VarPath
from . import pre_processor

from soleil.resolvers.module_resolver import ModuleResolver, SolConfModule
from soleil.resolvers.base import resolve as call_resolve

DEFAULT_EXTENSION = ".solconf"


def load_config(
    conf_path: PathSpec,
    package_name=None,
    overrides: Optional[List[OverrideSpec]] = None,
    resolve=True,
    promoted=True,
    _var_path=VarPath(),
):
    """
    Creates a new package with root at the parent of the spcified configuration path, and loads the specified configuration path as a module in that package.

    :param conf_path: The path of the module to load.
    :param package_name: The package name -- defaults to a random string.
    :param overrides: The overrides to apply when loading the module -- these will be overriden by any package-level overrides specified when creating the pacakge.

    (See :meth:`ConfigLoader.load` for the interpretation of parameters ``resolve`` and ``promoted``)
    """

    # Check path is a *.solconf file
    conf_path = Path(conf_path)
    if conf_path.suffix != DEFAULT_EXTENSION or not conf_path.is_file():
        raise ValueError(f"Expected a `*.solconf` file but received `{conf_path}`")

    #
    package_name = GLOBAL_LOADER.init_package(conf_path.parent, package_name, overrides)
    module_name = f"{package_name}.{conf_path.stem}"

    out = GLOBAL_LOADER.load(
        module_name, resolve=resolve, promoted=promoted, _var_path=_var_path
    )

    # Check that all overrides were used
    if resolve and (
        unused_ovrds := [
            _ovr
            for _ovr in GLOBAL_LOADER.package_overrides[package_name]
            if not _ovr.used
        ]
    ):
        raise ValueError(
            f"Unused overrides {', '.join(_x.source or _x.target.as_str() for _x in unused_ovrds)}"
        )

    return out


class ConfigLoader:
    """
    Loads solconf packages and applies CLI overrides.
    """

    modules: Dict[str, SolConfModule]
    """ Contains previously-loaded modules or package paths """
    package_roots: Dict[str, Path]
    """ Contains the roots of solconf pacakges """

    def __init__(self):
        """See the documentation for :func:`load_config`."""
        self.modules = {}
        self.package_roots = {}
        self.package_overrides = {}

    def init_package(
        self,
        path: Union[str, Path],
        name: Optional[str] = None,
        overrides: Optional[List[OverrideSpec]] = None,
    ):
        """
        Initializes a solconf package at the specified path and with the given name (random name by default).
        """
        name = name or uuid4().hex
        if name in self.package_roots:
            raise ValueError(
                f"Attempted to reinitialize existings solconf package `{name}`"
            )
        self.package_roots[name] = Path(path).resolve(strict=True)
        self.package_overrides[name] = eval_overrides(overrides or [], {}, {})
        return name

    def get_sub_module_path(self, abs_module_name, check_exists=True) -> Path:
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

    def load(
        self,
        abs_module_name: str,
        resolve: bool = True,
        promoted: bool = True,
        reqs: Optional[List[OverrideSpec]] = None,
        _var_path: Optional[str] = None,
        _root_config: Optional[SolConfModule] = None,
    ):
        """
        :param module_name: The absolute module name (e.g., ``package_name.sub_module_1.sub_module_2``)
        :param resolve: Return the model's resolved value if ``True``, otherwise the module itself.
        :param promoted: Whether to return the promoted member of teh full module. Only has an effect when ``resolve=False``.
        :param reqs: Default values for all :class:`req` members provided as part of load/submodule within a solconf file.
        :param _var_path: When loading a module from within another module, this will point to the variable/attribute name sequence relative to the root module. Used to apply overrides.
        :param _root_config: The root configuration of the module being loaded. Root configurations are the starting point where variable paths are resolved from.
        """

        # Create, parse and register the module
        if (module := self.modules.get(abs_module_name, None)) is None:
            module = self._parse_solconf_module(
                abs_module_name, _var_path, _root_config, reqs
            )
            self.modules[abs_module_name] = module

        # Execute the module
        if not module.__soleil_pp_meta__["executed"]:
            self._execute_solconf_module(module)

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

    def _parse_solconf_module(
        self,
        abs_module_name: str,
        var_path: Optional[str],
        root_config: Optional[SolConfModule],
        reqs: Optional[List[OverrideSpec]] = None,
    ):
        #
        module_path = self.get_sub_module_path(abs_module_name)

        # Instantiate the solconf module
        module = SolConfModule(
            abs_module_name,
            module_path,
            var_path,
            eval_overrides(reqs or [], {}, {}),
            root_config,
        )

        # Parse the code in the module
        with open(module.__file__, "rt") as fo:
            code = fo.read()
        tree = ast.parse(code)

        # Apply the pre-processor
        spp = pre_processor.SoleilPreProcessor(module_path)
        tree = spp.visit(tree)
        module.__soleil_pp_meta__["tree"] = tree
        module.__soleil_pp_meta__["executed"] = False
        module.__soleil_pp_meta__["promoted"] = spp.promoted_name

        # Append the imported ignores
        module.__soleil_default_hidden_members__.update(spp.imported_names)

        return module

    def _execute_solconf_module(self, module):
        # Execute the module
        exec(
            compile(
                module.__soleil_pp_meta__["tree"],
                filename=str(module.__file__),
                mode="exec",
            ),
            _globals := vars(module),
            _globals,
        )

        return module


GLOBAL_LOADER = ConfigLoader()
