from importlib import import_module
from uuid import uuid4

from pglib.validation import NoItem, checked_get_single
from .override import Handled, Override
import ast
from typing import Any, List, Optional, Union

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


class CLIOverrider(ast.NodeTransformer):
    position: List[str]
    overrides: List[Override]
    abs_module_name: str

    def __init__(
        self,
        overrides: Optional[List[Override]] = None,
        **kwargs,
    ):
        self.position = []
        self.overrides = list(overrides or [])
        super().__init__(**kwargs)

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        self.position.append(node.name)
        out = self.generic_visit(node)
        self.position.pop()
        return out

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
        # TODO: This will fail silently in the following situation:
        #
        # x:hidden  # CLI override assigned here
        # class x:  # ...but overriden here
        #     ...
        # x = 1     # ...or here
        #

        return self._visit_assign(node, node.target)

    def visit_Assign(self, node: ast.Assign) -> Any:
        if not len(node.targets) == 1:
            # Need to implement
            raise NotImplementedError("Only single assignments supported")
        return self._visit_assign(node, node.targets[0])

    def _visit_assign(self, node: Union[ast.Assign, ast.AnnAssign], target) -> Any:
        if not isinstance(target, ast.Name):
            # TODO (Document): This is a simplification to avoid CLI override inconsistencies where
            # an override assignment to a (nested) attribute (or entry) is itself overriden
            # in asubsequent statement.
            #
            # Example:
            # class A:
            #     a = 1 #CLI override would happen here
            # A.a = 2 # Override of possible CLI override
            #
            raise NotImplementedError(
                "Assignment to attributes or entries within *.solconf modules is not supported"
            )
        elif self.overrides:
            # Check if the value is overriden or rebind following a simple load or submodule.
            posn_str = ".".join(self.position + [target.id])
            node_binding_id = str(uuid4())
            for ovr in list(
                x for x in (self.overrides or []) if x.handled is not Handled.HANDLED
            ):
                if ovr.target == posn_str:
                    # Override existing value
                    node = self.override_assignment(node, ovr)
                elif (
                    ovr.target.startswith(posn_str)
                    and ovr.target[len(posn_str)] == "."
                    and isinstance(node.value, ast.Call)
                    and node.value.func.id in ["load", "submodule"]
                ):
                    # Rebind override to loaded module
                    #
                    # TODO (Document): Will fail when load or submodule are not called explicitly or directly.
                    # Example:
                    #     x = globals['load']('mod.submod')
                    #     y = load('mod.submod')[0]
                    #     y = fxn(load('mod', 'submod'))
                    node = self.rebind_override(
                        node,
                        ovr,
                        new_target=ovr.target[len(posn_str) + 1 :],
                        binding_id=node_binding_id,
                    )
                # TODO: Add cases to support nested assignment of non-loaded values, including subscripts.

            # The value is not overriden
            return self.generic_visit(node)
        else:
            return self.generic_visit(node)

    def override_assignment(self, node, ovr):
        # Override assignment
        if isinstance(node.value, ast.Call) and node.value.func.id == "submodule":
            node.value.args[1] = ast.parse(ovr.value).body[0].value
        else:
            node.value = ast.parse(ovr.value).body[0].value

        # Check preprocessor annotations
        if isinstance(node, ast.AnnAssign):
            ann = node.annotation
            if (
                isinstance(ann, ast.Tuple)  # target:(x,y,noid)
                and "noid" in (_x.id for _x in ann.elts if isinstance(_x, ast.Name))
            ) or (
                isinstance(ann, ast.Name) and ann.id == "noid"
            ):  # target:noid
                ovr.as_id = False

        ovr.handled = Handled.HANDLED
        self.overrides.remove(ovr)
        return node

    def rebind_override(self, node, ovr, new_target, binding_id):
        # Check that the node is not bound
        if (
            current := checked_get_single(
                (x for x in node.value.keywords if x.arg == "_overrides_binding_id"),
                raise_empty=False,
            )
        ) is not NoItem:
            # Node already bound -- ensure its the same binding id
            if current.value.value != binding_id:
                raise ValueError("Cannot rebind a bound node")
        else:
            # Add new binding id
            node.value.keywords.append(
                ast.keyword("_overrides_binding_id", ast.Constant(binding_id))
            )

        # (Re)bind the override
        ovr._binding_id = binding_id
        ovr.target = new_target
        ovr.handled = Handled.DELEGATED
        self.overrides.remove(
            ovr
        )  # Stops the override from being applied to other nodes
        # Future loads will create their own SoleilPreProcessor and add overrides.

        return node


class SoleilPreProcessor(GetImportedNames, CLIOverrider, ast.NodeTransformer):
    def visit(self, tree: ast.Module):
        tree = super().visit(tree)
        ast.fix_missing_locations(tree)
        return tree
