import ast
from dataclasses import dataclass
from typing import Dict, Any
import builtins
import operator as op
import numpy as np

# supported operators
MAX_EXPR_LEN = int(1e4)

# Exceptions


class UndefinedFunction(KeyError):
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
BUILTIN_ITERABLE_TYPES = (
    'list', 'tuple', 'dict', 'set')  # Require __iter__
"""
All these types from the ``builtins`` module are supported both as part of expressions and as node modifiers.
"""

DEFAULT_CONTEXT = {
    **{key: getattr(builtins, key) for key in BUILTIN_SCALAR_TYPES + BUILTIN_ITERABLE_TYPES}
}
"""
Contains the default context accessible to parsers.
"""


class _Unassigned:
    pass


@dataclass
class register:
    """
    Register a variable in the default context.

    Example:

    .. testcode::

      from soleil import register

      my_var = 'my variable'

      # As a stand-alone call
      register('my_var', my_var)

      # As a function decorator
      @register('my_function')
      def my_function(): pass

    """

    def __init__(self, name: str, value: Any = _Unassigned, *, overwrite: bool = False,
                 context: Dict[str, Any] = DEFAULT_CONTEXT):
        """
        :param name: The name of the variable in the context.
        :param overwrite:  Whether to overwrite the variable if it is already in the context.
        :param context: The context to modify.
        """

        self.name = name
        self.overwrite = overwrite
        self.context = context
        self.executed = False

        if value is not _Unassigned:
            self._register(value)

    def __call__(self, fxn):
        """
        Registers the input function.
        """
        self._register(fxn)
        return fxn

    def _register(self, value):
        if not self.overwrite and self.name in DEFAULT_CONTEXT:
            raise Exception(f'A variable with name `{self.name}` already exists in the context.')
        self.context[self.name] = value


class Parser:

    def __init__(self, extra_context=None):
        """
        :param extra_context: Extra variables to append to the default context. These will overwrite existing variables of the same name.

        .. warning:: Using python precision can result in system hangs from malicious input given Python's infinite precision (e.g., ``parser.eval('9**9**9**9**9**9**9')`` will hang).
        """
        self._operators = PYTHON_PRECISION
        self._context = {**DEFAULT_CONTEXT, **(extra_context or {})}

    def register(self, name, value, overwrite=False):
        register(name, value, overwrite=overwrite, context=self._context)

    def get_from_context(self, name, context=None):
        try:
            return (context or self._context)[name]
        except KeyError:
            raise UndefinedFunction(f'Name `{name}` undefined in parser context.')

    def eval(self, expr, extra_context=None):
        """
        Evaluates the python expression ``expr``.

        The parser's context is extended by ``extra_context`` if provided.
        """

        extended_context = {**self._context, **extra_context} if extra_context else None
        if len(expr) > MAX_EXPR_LEN:
            raise Exception('The input expression has length {len(expr)} > {MAX_EXPR_LEN}.')
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
            return func(
                *[eval_ctx(x) for x in node.args],
                *[eval_ctx(x) for x in getattr(node, 'starargs', [])],
                **{x.arg: eval_ctx(x.value) for x in node.keywords},
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
        else:
            raise UnsupportedPythonGrammarComponent(node)
