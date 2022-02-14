

.. doctest:: global_register

   >>> from soleil.solconf.parser import register, Parser

   # As a function
   >>> register('a', 3)

   # As a decorator
   >>> @register('x2')
   ... def x2(b):
   ...   return b*2

   >>> parser = Parser()
   >>> parser.safe_eval('x2(a)')
   6

.. testcleanup:: global_register

   from soleil.solconf.parser import DEFAULT_CONTEXT
   DEFAULT_CONTEXT.pop('a')
   DEFAULT_CONTEXT.pop('x2')

