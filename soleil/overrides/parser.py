import ast
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional, Tuple, Type
from jztools.py import strict_zip
from soleil._utils import Unassigned
from .variable_path import VarPath, Attribute, Subscript


class OverrideType(Enum):
    existing = 0
    """ Override an existing value """


@dataclass
class Override:
    """
    Contains a parsed override and components.
    """

    target: VarPath
    assign_type: OverrideType
    value_expr: ast.Expression
    source: Optional[str] = None
    """ The source code corresponding to this override, if available"""
    used: int = 0
    """ The number of times the override has been used -- can be used multiple times when overrides are shared by a spawned parent class and its child class """

    def get_value(self, _globals=None, _locals=None):
        """
        Extracts the assignment value from the specified globals and locals.
        """
        return eval(
            compile(self.value_expr, filename="<none>", mode="eval"), _globals, _locals
        )


class _RestrictedNodeVisitor(ast.NodeVisitor):
    """
    Checks that only certain node types are accessed.
    """

    default_nodes: Tuple[Type[ast.AST], ...] = (ast.Expr, ast.Module)
    """ Will call ``ast.NodeVisitor.generic_visit`` on these nodes """
    specialized_nodes: Tuple[Type[ast.AST], ...]
    """ A specialized method is implemented for these nodes """

    def __init_subclass__(cls) -> None:
        if not hasattr(cls, "specialized_nodes"):
            cls.specialized_nodes = tuple(
                [
                    getattr(ast, name[len("visit_") :])
                    for name in (_ for _ in vars(cls) if _.startswith("visit_"))
                ]
            )

        return super().__init_subclass__()

    @property
    def permitted_nodes(self):
        return (*self.default_nodes, *(getattr(self, "specialized_nodes", tuple())))

    def generic_visit(self, node):
        if isinstance(node, self.permitted_nodes):
            super().generic_visit(node)
        else:
            raise ValueError(f"Invalid node type {type(node)}")

        return node


class RefExtractor(_RestrictedNodeVisitor):
    """
    Parses a reference string, raising an error on invalid strings.

    Builds a list of references.
    """

    default_nodes = (
        *_RestrictedNodeVisitor.default_nodes,
        ast.Index,
        ast.Load,
        ast.Store,
    )

    _refs: VarPath

    @property
    def refs(self):
        return self._refs[::-1]

    def __init__(self, *args, **kwargs):
        self._refs = VarPath()
        super().__init__(*args, **kwargs)

    def visit_Attribute(self, node: ast.Attribute):
        if not isinstance(node.attr, str):
            raise TypeError(f"Invalid ast.Attribute.attr type {type(node.attr)}")
        self._refs.append(Attribute(node.attr))
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript):
        self._refs.append(Subscript())
        # Order of below calls is important
        self.visit(node.slice)  # Add the slice value first
        self.visit(node.value)  # Then append new references

    def visit_Constant(self, node: ast.Constant) -> Any:
        if not isinstance(node.value, expected := (int, str)):
            raise TypeError(
                f"Invalid type {type(node.value)} when expecting {expected}"
            )
        if (
            not isinstance(last_subs := self._refs[-1], Subscript)
            or last_subs.value is not Unassigned
        ):
            raise Exception("Orphan Constant node")
        last_subs.value = node.value

    def visit_Name(self, node: ast.Name):
        self._refs.append(Attribute(node.id))


class ValueVerifier(_RestrictedNodeVisitor):
    """Checks that a specified value expression is valid"""

    default_nodes: Tuple[Type[ast.AST], ...] = (
        ast.Constant,
        ast.Name,
        ast.Attribute,
        ast.Subscript,
        ast.BinOp,
        ast.operator,
        ast.Tuple,
        ast.List,
        ast.Load,  # Required for tuples, lists.
    )


class OverrideSplitter(_RestrictedNodeVisitor):
    """Splits python code containing one or more assignments into overrides, enforcing override syntax restrictions"""

    overrides: List[Override]

    def __init__(self):
        self.overrides = []

    def visit_Assign(self, node: ast.Assign):
        # Extract the target reference
        if len(node.targets) != 1:
            raise NotImplementedError("Only single-target assignments are supported.")
        target = node.targets[0]
        (ref_xtrctr := RefExtractor()).visit(target)

        # Verify that the value node is valid
        ValueVerifier().visit(node.value)

        self.overrides.append(
            Override(ref_xtrctr.refs, OverrideType.existing, ast.Expression(node.value))
        )
        return node


def parse_ref(ref: str):
    """
    Takes a reference such as ``'a.b[0].x`` and parses it into a sequence of attribute or item references.
    """

    try:
        tree = ast.parse(ref)

        # Apply the pre-processor
        ref_exctr = RefExtractor()
        tree = ref_exctr.visit(tree)
    except Exception as err:
        raise SyntaxError(f"Error parsing ref string `{ref}`") from err

    return ref_exctr.refs


def parse_overrides(overrides: str) -> List[Override]:
    """
    Takes code containing one or more assignment such as ``'a.b[0].x = a.c + 3'`` and returns a list of :class:`Overrides`
    """
    try:
        tree = ast.parse(overrides)

        # Apply the pre-processor
        splitter = OverrideSplitter()
        tree = splitter.visit(tree)

        # Append source expression
        # TODO: use ast.get_source_segment in the code below
        sources = [extract_string_expression(overrides, _expr) for _expr in tree.body]
        split_overrides = splitter.overrides
        for _ovr, _src in strict_zip(split_overrides, sources):
            _ovr.source = _src
    except Exception as err:
        raise SyntaxError(f"Error parsing override(s) `{overrides}`") from err

    return split_overrides


def extract_string_expression(source: str, expr: ast.Expr):
    # Extracts the string containing the override from a possibly multi-override string (e.g., a multi-line string or semi-colon separated string).
    if expr.lineno != expr.end_lineno:
        raise NotImplementedError(
            "Currently, only single-line expressions within multi-line overrides are supported"
        )
    lines = source.split("\n")
    return lines[expr.lineno - 1][expr.col_offset : expr.end_col_offset]
