from importlib import import_module
import ast
from typing import Union

SOLEIL_KEYWORDS = frozenset({"load", "submodule", "breakpoint"})


class GetImportedNames(ast.NodeVisitor):
    def __init__(self, **kwargs):
        self.imported_names = []
        super().__init__(**kwargs)

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


class AddTargetToLoads(ast.NodeTransformer):
    def _add_target_to_load(
        self, node: Union[ast.Assign, ast.AnnAssign], target_name: str
    ):
        # Injects the `_target` keyword argument to load() calls.
        # TODO: Need to ensure that the user has not re-defined load.
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
        if node.value is not None:
            node.value = ast.Call(
                ast.Name("override", ctx=ast.Load()),
                [ast.Constant(target_name), node.value],
                [],
            )
        return node

    def visit_Assign(self, node):
        if len(node.targets) > 1 or not isinstance(node.targets[0], ast.Name):
            # Currently, only single-target assignments are supported for simplicity
            raise NotImplementedError(
                "Multi-target assignments not currently supported"
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
            raise NotImplementedError("Unsupported type of annotated assignment")

        node = self._add_target_to_load(node, node.target.id)
        node = self._apply_override(node, node.target.id)

        return self.generic_visit(node)


class SoleilPreProcessor(GetImportedNames, AddTargetToLoads, ast.NodeTransformer):
    def visit(self, tree: ast.Module):
        return ast.fix_missing_locations(super().visit(tree))
