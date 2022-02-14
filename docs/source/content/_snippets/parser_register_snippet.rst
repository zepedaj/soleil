.. doctest::

   >>> from soleil.solconf.parser import Parser

   >>> parser = Parser()

   # The defined variables affect only `parser`.
   >>> parser.register('first', 'John')
   >>> parser.register('with_last', lambda x: f'{x} Doe')

   >>> parser.safe_eval('first')
   'John'

   >>> parser.safe_eval('with_last(first)')
   'John Doe'

   # Above defs not included in next instantiation
   >>> Parser().safe_eval('first')  
   Traceback (most recent call last):
   ...
   soleil.solconf.parser.UndefinedName: 'Name `first` undefined in parser context.'
