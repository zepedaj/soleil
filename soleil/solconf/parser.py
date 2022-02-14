import ast
from dataclasses import dataclass
from typing import Dict, Any
import builtins
import operator as op
import numpy as np

# supported operators
MAX_EXPR_LEN = int(2e2)

# Exceptions


class UndefinedName(KeyError):
    pass


class UnsupportedPythonGrammarComponent(TypeError):
    pass


PYTHON_PRECISION = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
                    ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
                    ast.USub: op.neg,
                    ast.Lt: op.lt, ast.LtE: op.le,
                    ast.Eq: op.eq, ast.NotEq: op.ne,
                    ast.Gt: op.gt, ast.GtE: op.ge}
"""
.. warning:: Python operators have infinite precision and can result in hangs when large computations are requested.
"""
# TODO: One solution to this problem is to use the finite-precision numpy operators when all arguments are numbers.

BUILTIN_SCALAR_TYPES = (
    'float', 'int', 'bool', 'bytes', 'str', 'slice')
"""
All these types from the ``builtins`` module are supported both as part of expressions and as node modifiers.
"""
BUILTIN_ITERABLE_TYPES = (
    'list', 'tuple', 'dict', 'set')  # Require __iter__
"""
All these types from the ``builtins`` module are supported both as part of expressions and as node modifiers.
"""

DEFAULT_CONTEXT = {
    **{key: getattr(builtins, key) for key in BUILTIN_SCALAR_TYPES + BUILTIN_ITERABLE_TYPES}
}
"""
The default context -- :class:`Parser` objects create a copy of this context upon instantiation to use as their own variable context. This context can be extended using :func:`register`. All :class:`Parser` objects instantiated after registering a named variable will have access to it.
"""


class _Unassigned:
    pass


def register(name: str, value: Any = _Unassigned, *, overwrite: bool = False,
             context: Dict[str, Any] = None):
    """
    Registers a variable in the specified context (:attr:`DEFAULT_CONTEXT` by default). Can be used as a function to register any variable type, or as a function decorator for convenience when registering functions and methods:

    .. include:: ../../_snippets/register_doctest.rst

    """

    context = DEFAULT_CONTEXT if context is None else context

    if value is not _Unassigned:
        # Called as a function
        _register(name, value, overwrite, context, do_return=False)
    else:
        # Called as a decorator
        return lambda value: _register(name, value, overwrite, context, do_return=True)


def _register(name: str, value: Any, overwrite: bool, context: Dict[str, Any], do_return: bool):
    if not overwrite and name in context:
        raise Exception(f'A variable with name `{name}` already exists in the context.')
    context[name] = value
    if do_return:
        return value


class Parser:
    """
    The Soleil Restricted Python Parser (SRPP) (see :ref:`SRPP`).
    """

    def __init__(self, extra_context=None):
        """
        :param extra_context: Extra variables to append to the default context. These will overwrite existing variables of the same name.

        .. warning:: Using python precision can result in system hangs from malicious input given Python's infinite precision (e.g., ``parser.safe_eval('9**9**9**9**9**9**9')`` will hang).
        """
        self._operators = PYTHON_PRECISION
        self._context = {**DEFAULT_CONTEXT, **(extra_context or {})}

    def register(self, name, value, overwrite=False):
        """
        Registers the specified variable in this parser's own copy of the variable context.

        .. rubric:: Example:

        .. include:: ../../_snippets/parser_register_snippet.rst

        """
        register(name, value, overwrite=overwrite, context=self._context)

    def get_from_context(self, name, context=None):
        try:
            return (context or self._context)[name]
        except KeyError:
            raise UndefinedName(f'Name `{name}` undefined in parser context.')

    def safe_eval(self, expr, extra_context=None):
        """
        Evaluates the python expression ``expr``.

        The parser's context is extended by ``extra_context`` if provided.
        """

        if len(expr) > MAX_EXPR_LEN:
            raise Exception('The input expression has length {len(expr)} > {MAX_EXPR_LEN}.')
        extended_context = {**self._context, **extra_context} if extra_context else self._context
        return self._eval(ast.parse(expr, mode='eval').body, extended_context)

    def _eval(self, node, context=None):

        # Bind _eval to context, if any.
        if context:
            def eval_ctx(node): return self._eval(node, context=context)
        else:
            eval_ctx = self._eval

        # Evaluate the node.
        if isinstance(node, ast.Num):  # <number>
            return node.n
        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            return self._operators[type(node.op)](
                eval_ctx(node.left),
                eval_ctx(node.right))
        elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
            return self._operators[type(node.op)](eval_ctx(node.operand))
        elif isinstance(node, ast.Call):
            func = eval_ctx(node.func)

            # Build args:
            args = []
            for x in node.args:
                getattr(args, 'extend' if isinstance(x, ast.Starred) else 'append')(eval_ctx(x))

            # Build kwargs
            kwargs = {}
            for x in node.keywords:
                kwargs.update({x.arg: eval_ctx(x.value)}
                              if x.arg is not None else
                              eval_ctx(x.value))

            return func(
                # Args
                *args,
                # Optional starargs (TODO: when is this used?)
                *[eval_ctx(x) for x in getattr(node, 'starargs', [])],
                # Kwargs
                **kwargs,
                # Optional kwargs (TODO: when is this used?)
                **{x.arg: eval_ctx(x.value) for x in getattr(node, 'kwargs', [])})
        elif isinstance(node, ast.Subscript):
            obj = eval_ctx(node.value)
            ref = eval_ctx(node.slice)
            return obj[ref]
        elif isinstance(node, ast.Name):
            return self.get_from_context(node.id, context)
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Tuple):
            return tuple(eval_ctx(x) for x in node.elts)
        elif isinstance(node, ast.Slice):
            return slice(
                None if node.lower is None else eval_ctx(node.lower),
                None if node.upper is None else eval_ctx(node.upper),
                None if node.step is None else eval_ctx(node.step))
        elif isinstance(node, ast.Index):
            return eval_ctx(node.value)
        elif isinstance(node, ast.Dict):
            return dict(
                (eval_ctx(_key), eval_ctx(_val))
                for _key, _val in zip(node.keys, node.values))
        elif isinstance(node, ast.List):
            return [eval_ctx(_elt) for _elt in node.elts]
        elif isinstance(node, ast.IfExp):
            if eval_ctx(node.test):
                return eval_ctx(node.body)
            else:
                return eval_ctx(node.orelse)
        elif isinstance(node, ast.Compare):
            left = eval_ctx(node.left)
            out = True
            for right, curr_op in zip(node.comparators, node.ops):
                right = eval_ctx(right)
                out = out and self._operators[type(curr_op)](left, right)
                if not out:
                    break
                else:
                    left = right
            return out
        elif isinstance(node, ast.Starred):
            return eval_ctx(node.value)
        else:
            raise UnsupportedPythonGrammarComponent(node)
