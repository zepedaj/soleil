.. doctest::
   :options: +NORMALIZE_WHITESPACE

   >>> from soleil.solconf.parser import Parser
   >>> import traceback

   >>> parser = Parser()

   # The defined variables affect only `parser`.
   >>> parser.register('first', 'John')
   >>> parser.register('with_last', lambda x: f'{x} Doe')

   >>> parser.safe_eval('first')
   'John'

   >>> parser.safe_eval('with_last(first)')
   'John Doe'

   # Above defs not included in next instantiation
   # soleil.solconf.parser.UndefinedName: 'Name `first` undefined in parser context.'
   # soleil.solconf.parser.EvalError: Error while attempting to evaluate expression `first`.
   >>> try:
   ...   Parser().safe_eval('first')
   ... except Exception as err:
   ...   print(traceback.format_exc()) # Print the traceback 
   Traceback (most recent call last):
   ...
   soleil.solconf.parser.UndefinedName: 'Name `first` undefined in parser context.'
   ...
   soleil.solconf.parser.EvalError: Error while attempting to evaluate expression `first`.

