from xerializer.cli_tools import ast_parser as mdl
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

            self.assertEqual(out := parser.eval(expr), val)
            self.assertIs(type(out), type(val))

    def test_undefined_function(self):
        parser = Parser()
        with self.assertRaisesRegex(mdl.UndefinedFunction, '.*`non_existing_fxn`.*'):
            parser.eval('non_existing_fxn("abc")')

    # def test_unsupported_grammar_component(self):
    #     with self.assertRaises(mdl.UnsupportedGrammarComponent):
    #         mdl.eval_expr()
