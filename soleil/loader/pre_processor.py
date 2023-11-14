from importlib import import_module
import ast

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
    def _add_target_to_load(self, node: ast.Assign):
        # Injects the `_target` keyword argument to load() calls.
        # TODO: Need to ensure that the user has not re-defined load.
        if (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "load"
        ):
            # Append `_target` keyword
            node.value.keywords.append(
                ast.keyword("_target", ast.Constant(node.targets[0].id))
            )
        return node

    def _apply_override(self, node: ast.Assign):
        node.value = ast.Call(
            ast.Name("override", ctx=ast.Load()),
            [ast.Constant(node.targets[0].id), node.value],
            [],
        )
        return node

    def visit_Assign(self, node):
        if len(node.targets) > 1 or not isinstance(node.targets[0], ast.Name):
            # Currently, only single-target assignments are supported for simplicity
            raise NotImplementedError(
                "Multi-target assignments not currently supported."
            )
        node = self._add_target_to_load(node)
        node = self._apply_override(node)

        return self.generic_visit(node)


class SoleilPreProcessor(GetImportedNames, AddTargetToLoads, ast.NodeTransformer):
    def visit(self, tree: ast.Module):
        return ast.fix_missing_locations(super().visit(tree))
