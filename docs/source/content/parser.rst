
.. currentmodule:: soleil.solconf

.. _SRPP:

Soleil Restricted Python Parser (SRPP)
=========================================

The **Soleil Restricted Python Parser (SRPP)** is used to evaluate :ref:`dstrings` (after stripping the prefix) and :ref:`raw key <raw key syntax>` modifer and type strings.

The SRPP supports a subset of the standard Python syntax and is built using Python's `Abstract Syntax Tree (ast) <https://docs.python.org/library/ast>`_ module. The main restrictions in the SRPP, meant to increase safety, are the following:

* Reduction in supported grammar components.
* Maximum parsed string length.
* Limited, user-extensible variable context.

Supported grammar components
-----------------------------

Supported grammar componets include :

* most binary and unary operators (``1+2``);
* comparison chains (``10>5<20==20``);
* function calls (``fxn(1,2,a=3)``, ``var_fxn(0,1,*a, b=3, **c))``);
* indices, including slice-based, (``a[::-1]``);
* tuples, dictionaries, lists and slices (``(1,2,3)``, ``{0:'a', None:2}``, ``[1,2,3]``, ``slice(1,5,2)``;
* ternary expressions (``0 if True else 2``).

Disallowed grammar components include:

* module imports (``import os``);
* attribute access (``obj.attrib``);
* variable assignment (``a=1``).

Default, parser and eval-time variable contexts
------------------------------------------------

Default context
^^^^^^^^^^^^^^^^^^^^

The SRPP evaluates all strings using an automatically generated variable context.  The **default variable** context, :attr:`~parser.DEFAULT_CONTEXT`, is assembled from

* the types in :attr:`~parser.BUILTIN_SCALAR_TYPES` and :attr:`~parser.BUILTIN_ITERABLE_TYPES`, as well as 
* the variables registered in modules :mod:`soleil.solconf.modifiers` and :mod:`soleil.solconf.functions`:

.. testsetup:: DEFAULT_CONTEXT

   from rich import print

.. doctest:: DEFAULT_CONTEXT
   :options: +NORMALIZE_WHITESPACE

   >>> from soleil.solconf.parser import DEFAULT_CONTEXT
   >>> print(DEFAULT_CONTEXT)
    {
        'NoneType': <class 'NoneType'>,
        'float': <class 'float'>,
        'int': <class 'int'>,
        'bool': <class 'bool'>,
        'bytes': <class 'bytes'>,
        'str': <class 'str'>,
        'slice': <class 'slice'>,
        'list': <class 'list'>,
        'tuple': <class 'tuple'>,
        'dict': <class 'dict'>,
        'set': <class 'set'>,
        'cwd': <function cwd at 0x...>,
        'values': <function values at 0x...>,
        'keys': <function keys at 0x...>,
        'dt64': <class 'numpy.datetime64'>,
        'range': <class 'range'>,
        'noop': <function noop at 0x...>,
        'parent': <function parent at 0x...>,
        'hidden': <function hidden at 0x...>,
        'load': <function load at 0x...>,
        'promote': <function promote at 0x...>,
        'choices': <class 'soleil.solconf.modifiers.choices'>,
        'types': <function types at 0x...>,
        'modifiers': <function modifiers at 0x...>,
        'raw_value': <function raw_value at 0x...>,
        'child': <function child at 0x...>,
        'extends': <class 'soleil.solconf.modifiers.extends'>,
        'fuse': <function fuse at 0x...>,
        'cast': <function cast at 0x...>
    }

New names can be added to the default context using :func:`parser.register`, which works as a function or a decorator:

.. include:: _snippets/register_doctest.rst


Parser context
^^^^^^^^^^^^^^^^

Upon instantiation of a :class:`~parser.Parser`, the parser creates a copy of the default context to use as its own variable context. New names can be added to this copy using :meth:`Parser.register <soleil.solconf.parser.Parser.register>`. Doing so does not alter the global :attr:`~parser.DEFAULT_CONTEXT`:

.. include:: _snippets/parser_register_snippet.rst


Eval-time context
^^^^^^^^^^^^^^^^^^

Variables can also be injected into the evaluation-time context when calling :meth:`Parser.safe_eval <parser.Parser.safe_eval>`. Variables injected into the evaluation-time context will only be available locally inside that call and not in the next call unless injected again:

.. doctest::
   :options: +NORMALIZE_WHITESPACE

   >>> from soleil.solconf.parser import Parser
   >>> import traceback
   
   >>> parser = Parser()

   # `a` and `b` definitions are local to that call
   >>> parser.safe_eval('a+b', {'a':1, 'b':2})
   3

   # They are not available in the next `parser.safe_eval` call
   # soleil.solconf.parser.UndefinedName: 'Name `a` undefined in parser context.'
   # soleil.solconf.parser.EvalError: Error while attempting to evaluate expression `a+b`.
   >>> try:
   ...   parser.safe_eval('a+b')
   ... except Exception as err:
   ...   print(traceback.format_exc()) # Print the traceback 
   Traceback (most recent call last):
   ...
   soleil.solconf.parser.UndefinedName: 'Name `a` undefined in parser context.'
   ...
   soleil.solconf.parser.EvalError: Error while attempting to evaluate expression `a+b`.


Soleil parsed nodes expose method :meth:`ParsedNode.safe_eval <soleil.solconf.nodes.ParsedNode.safe_eval>` that wraps :meth:`Parser.safe_eval <parser.Parser.safe_eval>` and automatically inject :ref:`cross-referencing variables <xref>` |ROOT_NODE_VAR_NAME|, |CURRENT_NODE_VAR_NAME| and |FILE_ROOT_NODE_VAR_NAME| into the eval-time variable context.
