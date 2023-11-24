import abc
from importlib import import_module
import ast
from pathlib import Path
from typing import Any, List, Tuple, Type, Union

__soleil_keywords__ = ["_soleil_override", "load", "promoted", "noid"]


class RaisesError(ast.NodeVisitor):
    path: Path

    def __init__(self, path, *args, **kwargs):
        self.path = path
        super().__init__(*args, **kwargs)

    def raise_error(
        self, msg: str, node: ast.AST, error_type: Type[Exception] = SyntaxError
    ):
        raise error_type(f'{msg} - File "{self.path}", line {node.lineno}')


class GetImportedNames(RaisesError, ast.NodeVisitor):
    """Keeps track of all imported names"""

    def __init__(self, *args, **kwargs):
        self.imported_names = []
        super().__init__(*args, **kwargs)

    def _visit_imports(self, node):
        for name in node.names:
            if name.name == "*":
                mdl = import_module(node.module)
                if hasattr(mdl, "__all__"):
                    self.imported_names.extend(mdl.__all__)
                else:
                    self.imported_names.extend(vars(mdl))
            else:
                self.imported_names.append(name.asname or name.name.split(".")[0])

        return node

    visit_Import = _visit_imports
    visit_ImportFrom = _visit_imports


class TrackQualName(RaisesError, ast.NodeVisitor):
    """
    Keeps track of the latest qualified name
    """

    def __init__(self, *args, **kwargs):
        self._qualname = []
        super().__init__(*args, **kwargs)

    @property
    def qualname(self):
        return ".".join(self._qualname)

    def from_qualname(self, name):
        return ".".join(self._qualname + [name])

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        class_name = node.name
        self._qualname.append(class_name)
        node = getattr(super(), "visit_ClassDef", self.generic_visit)(node)
        self._qualname.pop()
        return node


class ProcessClassDecorators(TrackQualName, abc.ABC):
    """
    Applies some processing when a class has known decorators
    """

    @abc.abstractmethod
    def process_class_decorators(self, node: ast.ClassDef, decorators: Tuple[str]):
        ...

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        if any(not isinstance(x, ast.Name) for x in node.decorator_list):
            self.raise_error(
                "Only name decorators currently supported", node, NotImplementedError
            )
        self.process_class_decorators(node, tuple(x.id for x in node.decorator_list))
        # NOTE: TrackQualName.visit_ClassDef must be called after this call
        # for the qualname check to work. This is enforced by the next call
        # and having ProcessClassDecorators derive from TrackQualName
        return getattr(super(), "visit_ClassDef", self.generic_visit)(node)


class ProcessModifiers(TrackQualName, abc.ABC):
    """
    Applies some processing when an assignment has annotations.
    """

    @abc.abstractmethod
    def process_modifiers(
        self, node: Union[ast.Assign, ast.AnnAssign], modifiers: Union[str, Tuple[str]]
    ):
        ...

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
        if not isinstance(node.target, ast.Name):
            self.raise_error("Unsupported annotation syntax", node, NotImplementedError)
        if isinstance(node.annotation, ast.Name):
            self.process_modifiers(node, node.annotation.id)

        elif isinstance(node.annotation, ast.Tuple):
            if not all(isinstance(x, ast.Name) for x in node.annotation.elts):
                self.raise_error("Annotations must be names or tuples of names", node)
            else:
                self.process_modifiers(
                    node, tuple(_x.id for _x in node.annotation.elts)
                )
        return getattr(super(), "visit_AnnAssign", self.generic_visit)(node)


class GetPromotedName(ProcessClassDecorators, ProcessModifiers):
    """
    Checks that a promoted name is promoted at the module level and
    registers the name.

    Keeps a dicitionary of (unpromoted) qualified names and modifiers (as strings).
    """

    _promoted_name = None

    @property
    def promoted_name(self):
        """The name of the promoted member"""
        return self._promoted_name

    def raise_non_root_member(self, node, target_name):
        self.raise_error(
            f"Attempted to promote non-root member `{target_name}`",
            node,
        )

    def set(self, name, node):
        if self.qualname:
            self.raise_non_root_member(node, f"{self.from_qualname(node.target.id)}")
        if self._promoted_name:
            self.raise_error(
                f'Multiple promotions detected ("{self._promoted_name}", "{name}")',
                node,
            )
        self._promoted_name = name

    def process_modifiers(self, node, modifiers):
        if (isinstance(modifiers, str) and modifiers == "promoted") or (
            isinstance(modifiers, tuple)
            and "promoted" in (x.id for x in node.annotation.elts)
        ):
            self.set(node.target.id, node)

        super().process_modifiers(node, modifiers)

    def process_class_decorators(self, node, decorators):
        if "promoted" in decorators:
            self.set(node.name, node)
        return super().process_class_decorators(node, decorators)


class GetNoids(GetPromotedName):
    _noids: List[str]
    """ All qualnames with noid modifiers """

    def __init__(self, *args, **kwargs):
        self._noids = []
        super().__init__(*args, **kwargs)

    @property
    def noids(self):
        if self.promoted_name:
            unpromoted = (".".split(_x) for _x in self._noids)
            return [_x[1:] for _x in unpromoted if _x[0] == self.promoted_name]
        else:
            return list(self._noids)

    def process_modifiers(
        self, node: Union[ast.Assign, ast.AnnAssign], modifiers: Union[str, Tuple[str]]
    ):
        if "noid" == modifiers or isinstance(modifiers, tuple) and "noid" in modifiers:
            self._noids.append(self.from_qualname(node.target.id))
        return super().process_modifiers(node, modifiers)

    def process_class_decorators(self, node: ast.ClassDef, decorators: Tuple[str]):
        if "noid" in decorators:
            self._noids.append(self.from_qualname(node.name))
        return super().process_class_decorators(node, decorators)


class ExtractDocStrings(TrackQualName):
    """Docstrings are only supported for classes and functions in python. This extractor adds support
    for sphinx-like global/class variable documentation"""

    def visit_Assign(self):
        pass

    def visit_AnnAssign(self):
        pass


class ProtectKeywords(RaisesError, ast.NodeVisitor):
    # path: Path
    # """ The path of the file being processed """

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store) and node.id in __soleil_keywords__:
            self.raise_error(f"Attempted to redefine soleil keyword `{node.id}`", node)
        if hasattr(super(), "visit_Name"):
            return super().visit_Name(node)
        else:
            return self.generic_visit(node)


class AddTargetToLoads(RaisesError, ast.NodeTransformer):
    """Injects the `_target` keyword argument to load() calls and converts all assignments to ``_soleil_override`` calls."""

    def _add_target_to_load(
        self, node: Union[ast.Assign, ast.AnnAssign], target_name: str
    ):
        # Injects the `_target` keyword argument to load() calls
        if (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "load"
        ):
            # Append `_target` keyword
            node.value.keywords.append(
                ast.keyword("_target", ast.Constant(target_name))
            )
        return node

    def _apply_override(self, node: Union[ast.Assign, ast.AnnAssign], target_name: str):
        # Converts all assignments to ``_soleil_override`` calls
        if node.value is not None:
            node.value = ast.Call(
                ast.Name("_soleil_override", ctx=ast.Load()),
                [ast.Constant(target_name), node.value],
                [],
            )
        return node

    def visit_Assign(self, node):
        if len(node.targets) > 1 or not isinstance(node.targets[0], ast.Name):
            # Currently, only single-target assignments are supported for simplicity
            self.raise_error(
                "Multi-target assignments not currently supported",
                node,
                NotImplementedError,
            )
        node = self._add_target_to_load(node, node.targets[0].id)
        node = self._apply_override(node, node.targets[0].id)

        return self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if (
            not isinstance(node.target, ast.Name)
            or not node.simple
            or not isinstance(node.target, ast.Name)
        ):
            # Currently, only single-target assignments are supported for simplicity
            self.raise_error(
                "Unsupported type of annotated assignment", node, NotImplementedError
            )

        node = self._add_target_to_load(node, node.target.id)
        node = self._apply_override(node, node.target.id)

        return self.generic_visit(node)


class SoleilPreProcessor(
    ProtectKeywords,
    GetNoids,
    GetPromotedName,
    GetImportedNames,
    AddTargetToLoads,
    ast.NodeTransformer,
):
    def visit(self, tree: ast.Module):
        return ast.fix_missing_locations(super().visit(tree))
