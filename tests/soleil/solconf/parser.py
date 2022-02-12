from soleil.solconf import parser as mdl
import yaml
from pathlib import Path
from unittest import TestCase


class Parser(mdl.Parser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register('echo', lambda *args, **kwargs: (args, kwargs))
        self.register('one', 1)


class TestFormat(TestCase):

    def test_all(self):
        with open(path := Path(__file__).parent / 'data/example.yaml', 'r') as stream:
            data = yaml.safe_load(stream)
            for key in ['type_decorated_keys_1',
                        'meta_decorated_keys',
                        'fully_decorated_keys_1',
                        'fully_decorated_keys_2']:
                multiple_syntaxes = data[key]
                [self.assertEqual(x, multiple_syntaxes[0]) for x in multiple_syntaxes]


class TestParser(TestCase):
    def test_parser(self):
        parser = Parser()
        for expr, val in [
                ('2^6', 4),
                ('2**6', 64),
                ('1 + 2*3**(4^5) / (6 + -7)', -5.0),
                ('echo("1.0",a=2)', (("1.0",), {'a': 2})),
                ('echo(1.0,a=2)', ((1.0,), {'a': 2})),
                ('echo(echo(1.0),a=2)', ((((1.0,), {}),), {'a': 2})),
                ('one', 1),
        ]:

            self.assertEqual(out := parser.safe_eval(expr), val)
            self.assertIs(type(out), type(val))

    def test_undefined_function(self):
        parser = Parser()
        with self.assertRaisesRegex(mdl.UndefinedName, '.*`non_existing_fxn`.*'):
            parser.safe_eval('non_existing_fxn("abc")')

    def test_supported_language_components(self):
        parser = Parser()

        for str_val in [
                # Lists, Dicts
                '{1:[0,1], 2:[2,3]}',  # Lists, dicts
                # Indexing
                '[0,1,2][0]',
                '[0,1,2][::2]',
                '[0,1,2,3][:3:2]',
                # Names
                'list(range(5))',
                # Constructs
                '1 if False else 2',
                '1 < 3 < 100 > 10 == 10 >= 9',
                '1 < 3 < 100 < 10 == 10 >= 9',
                # *args - TODO
                'slice(*[0, 10, 2])',
        ]:
            self.assertEqual(parser.safe_eval(str_val), eval(str_val))

    def test_args_kwargs_calls(self):
        parser = Parser()

        def fxn(a, b, *args, c=None, d=None, **kwargs):
            return {'a': a, 'b': b, 'args': args, 'c': c, 'd': d, 'kwargs': kwargs}
        parser.register('fxn', fxn)

        for call, expected in [
                ('fxn(0,1)',
                 {'a': 0, 'b': 1, 'args': tuple(), 'c': None, 'd': None, 'kwargs': {}}),
                #
                ('fxn(0,1,2,3,4)',
                 {'a': 0, 'b': 1, 'args': (2, 3, 4), 'c': None, 'd': None, 'kwargs': {}}),
                ('fxn(0,1,2,3,4,c=5,d=6,e=7)',
                 {'a': 0, 'b': 1, 'args': (2, 3, 4), 'c': 5, 'd': 6, 'kwargs': {'e': 7}}),
                # *args input
                ('fxn(0,1,*[2,3,4])',
                 {'a': 0, 'b': 1, 'args': (2, 3, 4), 'c': None, 'd': None, 'kwargs': {}}),
                # *kwargs input
                ('fxn(0,1,*[2,3,4],c=5,d=6,**{"e": 7})',
                 {'a': 0, 'b': 1, 'args': (2, 3, 4), 'c': 5, 'd': 6, 'kwargs': {'e': 7}}),
        ]:
            self.assertEqual(
                parser.safe_eval(call),
                expected
            )

    # def test_unsupported_grammar_component(self):
    #     with self.assertRaises(mdl.UnsupportedGrammarComponent):
    #         mdl.eval_expr()
