from .parser import Parser
from functools import partial


def register(name, namespace=None, doc=None):
    """
    Function decorator that registers a function using the specified name (and optionally namespace).

    .. test-code::

      @register('add', namespace='math')
      def add(a, b): return a+b
      assert Parser.get_fxn('numpy.add')(1,2)==3

      # The namespace can also be encoded directly in the name
      @register('math.sub')
      def sub(a, b): return a-b
      assert Parser.get_fxn('numpy.sub')(1,2)==3

    :param name: Relative (or fully/partially qualified) name.
    :param namespace: Namespace where ``name`` belongs.
    :param doc: For builtin functions, documentation string to add to manuals. By default, will take the function's doc-string.

    """
    fxn_name = (f'{namespace}.' if namespace else '') + f'{name}'

    def wrapper(fxn):
        Parser.register(fxn_name, fxn)
        return fxn

    return wrapper


def namespace(namespace_name):
    """
    Returns a function equivalent to ``lambda name, doc=None: register(name, namespace=namespace_name, doc=doc)`` that can be used to decorate multiple functions of the same namespace.

    .. rubric:: Example:

    .. test-code::

      from xerializer.cli_tools import Parser

      numpy_ns = namespace('numpy')

      @numpy_ns('add')
      def add(x,y): return x+y
      assert Parser.get_fxn('numpy.add')(1,2)==3

      @numpy_ns('sub')
      def sub(x,y): return x-y
      assert Parser.get_fxn('numpy.sub')(1,2)==3

    """
    return partial(register, namespace=namespace_name)
