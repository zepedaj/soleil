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


class SoleilPreProcessor(GetImportedNames, ast.NodeTransformer):
    def visit(self, tree: ast.Module):
        tree = super().visit(tree)
        ast.fix_missing_locations(tree)
        return tree
