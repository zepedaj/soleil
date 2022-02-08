from xerializer.cli_tools import parser as mdl
import numpy as np
from unittest import TestCase
import re


class TestAutonamePattern(TestCase):

    def test_doc(self):

        # Simple auto-name pattern
        sp = mdl.AutonamePattern('(?P<htag>Hello)', names=['htag'])

        # Composed auto-name pattern
        cp = mdl.AutonamePattern('{x} {x} {x} (?P<wtag>World)', {'x': sp}, names=['wtag'])

        # Match only the first pattern
        assert sp.view() == (sp0_expected := '(?P<htag_0>Hello)')
        assert re.match(sp0_actual := str(sp), 'Hello')
        assert sp0_actual == sp0_expected

        # Match composed pattern
        assert(
            cp.view() ==
            (cp0_expected :=
             '(?P<htag_1>Hello) (?P<htag_2>Hello) (?P<htag_3>Hello) (?P<wtag_0>World)'))
        assert re.match(
            cp0_actual := str(cp), 'Hello Hello Hello World')
        assert cp0_actual == cp0_expected
        assert sp.view() == '(?P<htag_4>Hello)'
        assert (
            cp.view() ==
            '(?P<htag_4>Hello) (?P<htag_5>Hello) (?P<htag_6>Hello) (?P<wtag_1>World)')

    def test_identifier_guarantee(self):
        NESTED = mdl.AutonamePattern('(?P<addend>[0-9])')
        str(NESTED)  # Advance the counter for illustration purposes.

        # 'my_letter' and 'my_value' are at the same nesting level; 'addend' is one level down.
        ap = mdl.AutonamePattern(r'(?P<my_letter>[a-z]) \= (?P<my_value>[0-9]) \+ {NESTED}', vars())
        match = re.match(str(ap), 'a = 1 + 2')

        # Tags at the same nesting level have the same suffix identifier
        assert match.groupdict() == {'my_letter_0': 'a', 'my_value_0': '1', 'addend_1': '2'}

    def test_doc__no_names(self):
        # Simple auto-name pattern
        sp = mdl.AutonamePattern('(?P<htag>Hello)')

        # Composed auto-name pattern
        cp = mdl.AutonamePattern('{x} {x} {x} (?P<wtag>World)', {'x': sp})

        # Match only the first pattern
        assert sp.view() == (sp0_expected := '(?P<htag_0>Hello)')
        assert re.match(sp0_actual := str(sp), 'Hello')
        assert sp0_actual == sp0_expected

        # Match composed pattern
        assert(
            cp.view() ==
            (cp0_expected :=
             '(?P<htag_1>Hello) (?P<htag_2>Hello) (?P<htag_3>Hello) (?P<wtag_0>World)'))
        assert re.match(
            cp0_actual := str(cp), 'Hello Hello Hello World')
        assert cp0_actual == cp0_expected
        assert sp.view() == '(?P<htag_4>Hello)'
        assert (
            cp.view() ==
            '(?P<htag_4>Hello) (?P<htag_5>Hello) (?P<htag_6>Hello) (?P<wtag_1>World)')


class TestPxs(TestCase):
    def test_all(self):
        for name, matches, non_matches in [
                ('VARNAME', vnm := ('abc0', '_abc0'), vnnm := ('0abc',)),
                ('NS_VARNAME', vnm+('abc0.def1',), vnnm+('abc.0abc', 'abc.', 'abc.def1.')),
                # Any string will match zero-slashes not preceded by slash
                # at the start of the string, including odd slashes. Skipping
                # Non-matching tests for even slashes.
                ('EVEN_SLASHES',
                 _even := ('', r'\\', r'\\\\', r'\\\\\\'),
                 _odd := ('\\', '\\'*3)),
                ('ODD_SLASHES', _odd, _even),
                ('ATTR',
                 ('$abc', r'\\$abc', r'\\\\$abc.def', '$abc'),
                 (r'\$abc', r'\\\$abc.def0', '$0abc')),
                ('UNQUOTED_LITERAL',
                 ('abc', r'a\$', r'\$b', r'a\#', r'\#b', r'\'a', r'a\"bc', r'a\,', r"a\""),
                 ("'abc'", '"abc"', "a'bc", 'a"bc', r'a\\$', r'a b', r'a,', ',', ',,', '')),
                ('QUOTED_LITERAL',
                 ("'abc'", '"a$"', "'#b'", "'\\#'", '"abc"', '"ab\"c"', r'"a\""', "'()'"),
                 ("'abc", 'abc"', 'a\\$' "'a'bc'", "")),
                ('ARG_LIST',
                 ('abc,def,xyz', '1,234,abc', "1,'abc', xyz",
                  "1,'()'",
                  "1,'()',c,5a3,'$f()'"),
                 (',', ' , ' 'a,,b', 'a=1', 'a=1,b', '')),
                ('KWARG_LIST',
                 ('abc=1, def=2,ghi=abc', 'abc=1',),
                 ('abc, def', 'abc 1, def=2,ghi=abc', ''))
        ]:
            [self.assertTrue(re.match('^'+str(getattr(mdl.pxs, name))+'$', match))
             for match in matches]
            [self.assertFalse(re.match('^'+str(getattr(mdl.pxs, name))+'$', non_match))
             for non_match in non_matches]

    def test_fxn_call(self):

        for value, arg_list_str, kwarg_list_str in [
                ('$add()', None, None),
                ('$add(a,b,c)', 'a,b,c', None),
                ('$add(a=1)', None, 'a=1'),
                ('$add(a=1,b=2)', None, 'a=1,b=2'),
                ('$add(a,b,c,d=1,b=2)', 'a,b,c', 'd=1,b=2'),
        ]:
            self.assertIsNotNone(match := re.fullmatch(mdl.Function.FXN_PATTERN, value))
            self.assertEqual(match['arg_list_0'], arg_list_str)
            self.assertEqual(match['kwarg_list_0'], kwarg_list_str)
        for value in [
                '$add(,)',
                '$add(,a)',
                '$add(a=1,b)',
                '$add($sub)',
                '$add(1,2,$a())',
        ]:
            match = re.fullmatch(mdl.Function.FXN_PATTERN, value)
            self.assertIsNone(match)


class TestFunction(TestCase):

    def test_cast_value(self):
        assert 'abc' == mdl.Function.cast_value('abc')
        assert 'abc' == mdl.Function.cast_value("'abc'")
        assert 1 == mdl.Function.cast_value('1')
        assert 1.1 == mdl.Function.cast_value('1.1')
        assert True is mdl.Function.cast_value('true')
        assert None is mdl.Function.cast_value('null')

    def test_get_args(self):
        for value, arg_list, kwarg_list in [
                ('$add()', [], {}),
                ('$add(a,b,c)', ['a', 'b', 'c'], {}),
                ("$add(1,'()',c,5a3,'$f()')", [1, '()', 'c', '5a3', '$f()'], {}),
                ('$add(a=1)', [], {'a': 1}),
                ('$add(a=1,b=2)', [], {'a': 1, 'b': 2}),
                ('$add(a,b,c,d=1,b=2)', ['a', 'b', 'c'], {'d': 1, 'b': 2}),
        ]:
            self.assertIsNotNone(match := re.fullmatch(mdl.Function.FXN_PATTERN, value))
            func = mdl.Function(match)
            self.assertEqual(func.get_args(), arg_list)
            self.assertEqual(func.get_kwargs(), kwarg_list)


class TestParser(TestCase):
    def test_all(self):
        parser = mdl.Parser()

        # Simple
        for in_str, expc_val, expc_type in [
                # Simple
                ('$dt64(2020-10-10)', np.datetime64('2020-10-10'), np.datetime64),
                ('true',  'true', str),
                ('$bool("true")',  True, bool),
                ('$bool(true)',  True, bool),
                ('$float(1)',  1.0, float),

                # Compound
                ('abc$bool("true")def',  'abcTruedef', str),
                ('abc$bool(val="true")def',  'abcTruedef', str),
        ]:
            self.assertEqual(out_val := parser.parse(in_str), expc_val)
            self.assertIs(type(out_val), expc_type)
