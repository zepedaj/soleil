from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, List, Union
import ast
from uuid import uuid4
from soleil.loader.override import Handled, Override
from soleil._utils import PathSpec
import importlib.util
import importlib.machinery
import importlib._bootstrap
import sys
from . import pre_processor

from soleil.resolvers.module_resolver import ModuleResolver, SolConfModule
from soleil.resolvers.base import resolve as call_resolve

DEFAULT_EXTENSION = ".solconf"
DEFAULT_PACKAGE_NAME = "solconf"


def load_config(
    conf_path: PathSpec,
    package_name=DEFAULT_PACKAGE_NAME,
    overrides: Optional[List[str]] = None,
    reqs: Optional[Dict[str, Any]] = None,
    resolve=True,
):
    """
    Creates a new instance of the solconf module at the specfied path.

    :param conf_path: A file with solconf extension. The package will implicitly be assigned to the directory of this file.
    :param package_name: [``'solconf'``] The package name.
    :param resolve: [``True``] Whether the resolve the module.
    """

    conf_path = Path(conf_path)

    if (is_dir := conf_path.is_dir()) or (
        (is_file := conf_path.is_file()) and conf_path.suffix != DEFAULT_EXTENSION
    ):
        raise ValueError(f"Expected a `*.solconf` file but received `{conf_path}`")
    elif not is_dir and not is_file:
        raise FileNotFoundError(conf_path)

    package_root = conf_path.parent
    sub_module_name = conf_path.stem
    config_loader = ConfigLoader(
        package_root, package_name=package_name, overrides=overrides
    )
    module_name = f"{package_name}.{sub_module_name}"

    return config_loader.load(module_name, resolve=resolve, reqs=reqs)


def random_name():
    """Use for random solconf package names"""
    return uuid4().hex


class ConfigLoader:
    """
    Loads solconf packages and applies CLI overrides.
    """

    overrides: List[Override]
    modules: Dict[str, Union[SolConfModule, Path]]
    """ Contains previously-loaded modules or package paths """

    def __init__(
        self,
        package_root: Path,
        package_name=DEFAULT_PACKAGE_NAME,
        overrides: Optional[List[str]] = None,
    ):
        """See the documentation for :func:`load_config`."""
        self.modules = {}
        self.package_name = (
            package_name if isinstance(package_name, str) else package_name()
        )
        self.package_root = Path(package_root)
        if not self.package_root.is_dir():
            raise ValueError(f"No solconf package at {self.package_root}.")
        self.overrides = [Override.build(_x) for _x in overrides or []]

    def get_sub_module_path(self, abs_module_name, check_exists=True):
        components = abs_module_name.split(".", -1)
        sub_packages = components[:-1]
        module_name = components[-1]
        module_path = self.package_root.joinpath(
            *sub_packages[1:], module_name + DEFAULT_EXTENSION
        )

        # Ensure the package corresponds to this loader's package
        if sub_packages[0] != self.package_name:
            raise ValueError(
                f"Attempted to load package {sub_packages[0]} from loader for `{self.package_name}`"
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
        reqs=None,
        _overrides_binding_id: Optional[str] = None,
    ):
        """
        :param module_name: The absolute module name (e.g., ``package_name.sub_module_1.sub_module_2``)
        :param resolve: Return the model's resolved value if ``True``, otherwise the module itself.
        :param reqs: The values for the required module members.
        """

        sub_module_path = self.get_sub_module_path(abs_module_name)

        # Create the module
        module = self._build_solconf_module(sub_module_path, abs_module_name, reqs=reqs)

        # Exec the module code
        self._exec_solconf_module(module, _overrides_binding_id=_overrides_binding_id)

        # Resolve the module
        if resolve:
            return call_resolve(module)
        else:
            return module

    def _build_solconf_module(self, file_path: PathSpec, module_name: str, reqs=None):
        """
        :param path: The path to the file.
        :param module_name: [Default is ``'solconf.<file_path stem>'``] The name of the module in python. A package name can be pre-pended to the module-name with a '.' separator. After calling this function, the module can be imported from any other module using ``import <module_name>``.
        """

        if module_name in sys.modules:
            # The conf module was previously loaded.
            module = sys.modules[module_name]
            if not isinstance(module, SolConfModule):
                raise ValueError(
                    f"The specified module `{module_name}` exists in `sys.modules` and is not a solconf module"
                )
            if (loaded_path := Path(module.__file__)) != (
                requested_path := Path(file_path)
            ):
                raise ValueError(
                    f"The specified solconf module `{module_name}` was previously "
                    f"loaded from a path `{loaded_path}` that is not the requested path `{requested_path}`."
                )
            if ModuleResolver(module)._get_required_member_names():
                raise ValueError(
                    f"Solconf modules with required members can only be loaded once. You can use `import {module.__name__}` to retrieve the previously-loaded solconf module"
                )

        else:
            # The conf moudle needs to be instantiated.
            file_path = Path(file_path)

            # spec = importlib.util.spec_from_file_location(module_name, file_path)
            if (
                spec := importlib.util.spec_from_loader(
                    module_name,
                    importlib.machinery.SourceFileLoader(module_name, str(file_path)),
                )
            ) is None:
                raise Exception(
                    f"Failed to load module {module_name} from path {file_path}."
                )

            #
            # Create the module.
            #
            # The default module creation approach
            #    module = importlib.util.module_from_spec(spec)
            #  calls private function _init_module_attrs internally. Setting
            #    module.__file__ = str(file_path.absolute())
            #    module.__name__ = spec.name
            #  avoids calling this function but might create problems.
            #

            module = SolConfModule(spec.name, loader=self, reqs=reqs)
            importlib._bootstrap._init_module_attrs(spec, module)
            sys.modules[module_name] = module

        return module

    def _exec_solconf_module(self, module: SolConfModule, _overrides_binding_id):
        with open(module.__file__, "rt") as fo:
            code = fo.read()
        tree = ast.parse(code)

        # Parse overrides
        overrides = [
            _ovr for _ovr in self.overrides if _ovr._binding_id == _overrides_binding_id
        ]

        # Apply the pre-processor
        spp = pre_processor.SoleilPreProcessor(overrides=overrides)
        tree = spp.visit(tree)

        def _check_overrides_handled(valid_states: Iterable[Handled]):
            if unhandled_overrides := [
                x for x in overrides if x.handled not in valid_states
            ]:
                raise Exception(
                    f"Could not handle the following overrides: {', '.join(f'`{x.source}`' for x in unhandled_overrides)}"
                )

        # Check that all overrides were handled or delgated
        _check_overrides_handled([Handled.HANDLED, Handled.DELEGATED])

        # Execute the module
        exec(compile(tree, filename=str(module.__file__), mode="exec"), module.__dict__)

        # Check that all overrides were handled
        _check_overrides_handled([Handled.HANDLED])

        # Append the imported ignores
        module.__soleil_default_hidden_members__.update(spp.imported_names)
