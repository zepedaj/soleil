from pathlib import Path
from typing import Any, Dict, Optional, List, Union
import ast
from uuid import uuid4
from soleil._utils import PathSpec, Unassigned

from soleil.resolvers._overrides.overrides import OverrideSpec, eval_overrides
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
    _qualname=None,
):
    """
    Creates a new package with root at the parent of the spcified configuration path, and loads the specified configuration path as a module in that package.

    :param conf_path: The path of the module to load.
    :param package_name: The package name -- defaults to a random string.
    :param overrides: The overrides to apply when loading the module.

    (See :meth:`ConfigLoader.load` for the interpretation of parameters ``resolve`` and ``promoted``)
    """

    # Check path is a *.solconf file
    conf_path = Path(conf_path)
    if conf_path.suffix != DEFAULT_EXTENSION or not conf_path.is_file():
        raise ValueError(f"Expected a `*.solconf` file but received `{conf_path}`")

    #
    package_name = GLOBAL_LOADER.init_package(conf_path.parent, package_name, overrides)
    module_name = f"{package_name}.{conf_path.stem}"

    return GLOBAL_LOADER.load(
        module_name, resolve=resolve, promoted=promoted, _qualname=_qualname
    )


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
        abs_module_name,
        resolve=True,
        promoted=True,
        _qualname=None,
    ):
        """
        :param module_name: The absolute module name (e.g., ``package_name.sub_module_1.sub_module_2``)
        :param resolve: Return the model's resolved value if ``True``, otherwise the module itself.
        :param promoted: Whether to return the promoted member of teh full module. Only has an effect when ``resolve=False``.
        :param _qualname: When loading a module from within another module, this will point to the variable/attribute name sequence relative to the root module. Used to apply overrides.
        """

        sub_module_path = self.get_sub_module_path(abs_module_name)

        # Create the module
        if (
            module := self._get_solconf_module(abs_module_name, sub_module_path)
        ) is None:
            # Build and register the module code
            module = self._build_solconf_module(
                abs_module_name, sub_module_path, _qualname
            )
        elif self.package_overrides[module.__package__]:
            # Reasons - Not clear what to do if
            #  1) overrides were or are specified and
            #  2) the module's __soleil_qualname__ used to find override targets would not be uniquely defined.
            raise NotImplementedError(
                "Reloading solconf packages not currently supported."
            )

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

    def _get_solconf_module(self, abs_module_name: str, module_path: Path):
        """
        Returns a previously-built module or ``None`` if not previously-built.

        :param path: The path to the file.
        :param abs_module_name: [Default is ``'solconf.<module_path stem>'``] The name of the module in python. A package name can be pre-pended to the module-name with a '.' separator. After calling this function, the module can be imported from any other module using ``import <abs_module_name>``.
        """

        module = None

        if abs_module_name in self.modules:
            # The conf module was previously loaded.
            module = self.modules[abs_module_name]
            if (loaded_path := Path(module.__file__)) != module_path:
                # The previous load path differs
                raise ValueError(
                    f"The specified solconf module `{abs_module_name}` was previously "
                    f"loaded from a path `{loaded_path}` that is not the requested path `{module_path}`."
                )
            if ModuleResolver(module)._get_required_member_names():
                # The module has required vars that need to be injected
                raise ValueError(
                    f"Solconf modules with required members can only be loaded once."
                )

        return module

    def _build_solconf_module(
        self, abs_module_name: str, module_path: Path, qualname: Optional[str]
    ):
        # Instantiate the solconf module

        module = SolConfModule(abs_module_name, module_path, qualname)
        self.modules[abs_module_name] = module

        # Execute the code in the module
        with open(module.__file__, "rt") as fo:
            code = fo.read()
        tree = ast.parse(code)

        # Apply the pre-processor
        spp = pre_processor.SoleilPreProcessor(module_path)
        tree = spp.visit(tree)

        # Execute the module
        exec(
            compile(tree, filename=str(module.__file__), mode="exec"),
            _globals := vars(module),
            _globals,
        )

        # Append the imported ignores
        module.__soleil_default_hidden_members__.update(spp.imported_names)

        return module


GLOBAL_LOADER = ConfigLoader()
