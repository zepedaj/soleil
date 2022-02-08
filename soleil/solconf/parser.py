"""
This parser operates as follows

1. Parse YAML file to container.
2. For each value string in the container: loop:
  a. Find an internal non-nested function call (exit loop if none found).
  b. Pass each argument value through the YAML pre-processor.
  c. Execute the function with the YAML-parsed values.
3. If the string consisted entirely of a function string, return the function's output.
4. Otherwise, convert all returned values to function strings and insert them in place of the function string.
"""

import re
import pglib.validation as pgval
from contextlib import ExitStack
from dataclasses import dataclass, field
from threading import RLock, Lock
from typing import Optional, Tuple, Dict, Union, Callable, Any
import yaml


def _n(name, expr):
    return f'(?P<{name}>{expr})'


@dataclass
class AutonamePattern:
    """
    Represents a pattern with named groups that have sequential numbers automatically attached to them as suffixes. The numbers are guaranteed to be the same for tags that appear at the same nesting level. Other than that, no guarantees are provided about their order, except that it should be sequential. **Example:**

    .. test-code::

        NESTED = mdl.AutonamePattern('(?P<addend>[0-9])')
        str(NESTED)  # Advance the counter for illustration purposes.

        # 'my_letter' and 'my_value' are at the same nesting level; 'addend' is one level down.
        ap = mdl.AutonamePattern(
            r'(?P<my_letter>[a-z]) \\= (?P<my_value>[0-9]) \\+ {NESTED}', vars())
        match = re.match(str(ap), 'a = 1 + 2')

        # Tags at the same nesting level have the same suffix identifier
        assert match.groupdict() == {'my_letter_0': 'a', 'my_value_0': '1', 'addend_1': '2'}

    The pattern can also contain placeholders for other :class:`AutoName` patterns using a syntax similar to the ``str.format`` syntax.

    .. warning:: Calling the meth:`__str__` method of this object (even implicitly through ``print(obj)``) will modify the object by advancing the counter. This enables support for situations where the same nested pattern is used more than once in the same expression, e.g., ``'{pattern}{pattern}'``

    .. test-code::

        # Simple auto-name pattern
        sp = mdl.AutonamePattern('(?P<htag>Hello)', ['htag'])

        # Composed auto-name pattern
        cp = mdl.AutonamePattern('{x} {x} {x} (?P<wtag>World)', ['wtag'], {'x': sp})

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
    """

    pattern: str
    nested_patterns: Dict[str, 'AutonamePattern'] = field(default_factory=dict)
    names: Optional[Tuple[str]] = None
    _k: int = 0
    _lock: RLock = field(default_factory=RLock)
    _frozen: bool = False

    def next_name(self, name):
        """
        Generates the next auto-numbered name derived from ``name``.
        """
        return self.name_builder(name, self._k)

    @classmethod
    def name_builder(cls, name, identifier):
        """
        Generates the name derived from ``name`` for the given ``identifier``.
        """
        return f'{name}_{identifier}'

    @classmethod
    def get_derived_tags(cls, base_tag: str, match: re.Match):
        tag_pattern = re.compile(cls.name_builder(base_tag, r'\d+'))
        return [x for x in match.groupdict().keys() if re.fullmatch(tag_pattern, x)]

    @classmethod
    def get_single(cls, base_tag: str, match: re.Match):
        """
        Returns the value of id-suffixed version of ``base_tag``, checking first that a single such tag exists in ``match``.
        """
        return match[cls.get_single_tag(base_tag, match)]

    @classmethod
    def get_single_tag(cls, base_tag: str, match: re.Match):
        """
        Returns the id-suffixed version of ``base_tag``, and checks that a single such tag exists in ``match``.
        """
        return pgval.checked_get_single(
            AutonamePattern.get_derived_tags(base_tag, match))

    def view(self):
        """
        Compiles the pattern to a string and without advancing the counters.
        """
        with ExitStack() as stack:
            all_patterns = [self]+list(self.nested_patterns.values())
            [stack.enter_context(x._lock) for x in all_patterns if not isinstance(x, str)]
            all_ks = [(x, x._k) for x in all_patterns]
            try:
                return str(self)
            finally:
                for (x, _k) in all_ks:
                    x._k = _k

    def __str__(self):
        """
        Compiles the pattern to a string and advances the counter.
        """

        with self._lock:

            # Replace names in pattern
            NAMES = (
                '|'.join(re.escape(x) for x in self.names)
                if self.names
                else r'[a-zA-Z]\w*')

            # Substitute groups
            out = self.pattern
            for GROUP_PREFIX, GROUP_SUFFIX in [
                    ('(?P<', '>'),  # Replaces (?P<name> by (?P<name_k>
                    ('(?P=', ')'),  # Replaces (?P=name) by (?P=name_k)
                    ('(?(', ')'),  # Replaces (?P=name) by (?P=name_k)
            ]:
                out = re.sub(
                    f"(?P<prefix>({pxs.EVEN_SLASHES}|^|[^{pxs.SLASH}]))"
                    f"{re.escape(GROUP_PREFIX)}(?P<name>{NAMES}){re.escape(GROUP_SUFFIX)}",
                    lambda x: f"{x['prefix']}{GROUP_PREFIX}{self.next_name(x['name'])}{GROUP_SUFFIX}",
                    out)

            # Replace nested patterns
            out = out.format(**self.nested_patterns)

            #
            if not self._frozen:
                self._k += 1

            return out


class pxs:
    """
    Contains base regex patterns.
    """

    # abc0, _abc0 (not 0abc)
    VARNAME = r'[a-zA-Z_]+\w*'

    # Matches VARNAME's and fully qualified versions
    # abc0.def1 (not abc.0abc, abc., abc.def1. )
    NS_VARNAME = AutonamePattern(
        r'{VARNAME}(\.{VARNAME})*(?!\.)(?!\w)', vars())

    # \\, \\\\, \\\\\\, not \, \\\
    SLASH = r'\\'
    EVEN_SLASHES = r'(?<!\\)(\\\\)*'
    ODD_SLASHES = r'\\(\\\\)*'

    # $abc, \\$abc, \\\\$abc.def
    ATTR = AutonamePattern(
        r"(?P<slash>{EVEN_SLASHES})\$(?P<name>{NS_VARNAME})", vars())

    # abc, a\$, \#b, \'a, a\"bc, a\, not 'abc', "abc", a'bc, a"bc, a\\, a,$
    UNQUOTED_LITERAL = (
        '('
        # No un-escaped spaces, $, #, =, ', ", (, ), \
        '[^' + (_qchars := r'\s\$\#\=\'\"\,\(\)\\' + ']|') +
        # A sequence of escape sequences
        f'({ODD_SLASHES}[{_qchars}])+'
        ')+'
    )

    # 'abc', "a$", '#b', '\#', "abc", not 'abc, abc", a\\$ 'a'bc'
    # r'(?P<q>(?P<sq>\')|(?P<dq>\"))((?(sq)\"|\')|[^\\])*(?P=q)'
    QUOTED_LITERAL = AutonamePattern(
        r'(?P<q>(?P<sq>\')|(?P<dq>\"))('
        # Non-quote
        + (non_quote := r'(?(sq)\"|\')' '|') +
        # Non-slash
        r'[^\\]' '|'
        # Odd-slashes-escaped non-slash char (including quote)
        r'{ODD_SLASHES}[^\\]' '|'
        # Even number of slashes followed by non-quote
        '{EVEN_SLASHES}' + non_quote +
        ')*?(?P=q)', vars())
    # $fxnname(arg), $fxnname(arg0, arg1), $fxnname(arg0, ... kwarg0=val0, ...)
    #

    # A string literal
    # "abc, def, '123' "
    LITERAL = AutonamePattern(
        '({UNQUOTED_LITERAL}|{QUOTED_LITERAL})', vars())

    # Arguments in argument lists are interpreted as YAML strings.
    LITERAL_ARG = LITERAL
    ARG_LIST = AutonamePattern(
        r'({LITERAL_ARG}(\s*,\s*{LITERAL_ARG})*)', vars())

    LITERAL_KWARG = AutonamePattern(
        r'(?P<kw_name>{VARNAME})\s*=\s*(?P<kw_val>{LITERAL})', vars())
    KWARG_LIST = AutonamePattern(
        ARG_LIST.pattern.format(LITERAL_ARG='{LITERAL_KWARG}'), vars())

    # Matches a function call where all arguments have been resolved (i.e., a non-nested function call).
    FXN_CALL = AutonamePattern(
        r'\$(?P<fxn>{NS_VARNAME})\('
        r'\s*(?P<arg_list>{ARG_LIST})?\s*((?(arg_list),\s*)(?P<kwarg_list>{KWARG_LIST}))?\s*'
        r'\)', vars())


class Function:

    FXN_PATTERN = re.compile(f'{pxs.FXN_CALL}')
    """
    The compiled regexp pattern representing a function call.
    """
    LITERAL_ARG_PATTERN = re.compile(str(pxs.LITERAL_ARG))
    LITERAL_KWARG_PATTERN = re.compile(str(pxs.LITERAL_KWARG))

    def __init__(self, match: Union[re.Match, str]):
        """
        Supports processing a match to regular expression :attr:`pxs.FXN_CALL`. These matches do not contain nested function calls.

        Each argument and keyword argument value is first processed as a stand-alone YAML string using :meth:`cast_value`.
        """
        if not isinstance(match, re.Match):
            raise TypeError("Expected a re.Match object!")
        self.match = match

    @property
    def name(self):
        return self.match[AutonamePattern.get_single_tag('fxn', self.match)]

    @staticmethod
    def cast_value(value):
        """
        Casts value using yaml processing rules.

        Example:

        .. test-code::

          assert 'abc' == Function.cast_value('abc')
          assert 1 == Function.cast_value('1')
          assert 1.1 == Function.cast_value('1.1')
          assert True is Function.cast_value('true')
          assert None is Function.cast_value('null')

        """
        return yaml.safe_load(value)

    @classmethod
    def _cast_kwarg_match(cls, match: re.Match):
        kw_name_tag = AutonamePattern.get_single_tag('kw_name', match)
        kw_val_tag = AutonamePattern.get_single_tag('kw_val', match)
        return match[kw_name_tag], cls.cast_value(match[kw_val_tag])

    def get_args(self) -> list:
        """
        Return all cast argument values.
        """
        arg_list_tag = AutonamePattern.get_single_tag('arg_list', self.match)
        if arg_list := self.match[arg_list_tag]:
            return [
                self.cast_value(arg_val.group()) for arg_val in
                re.finditer(
                    self.LITERAL_ARG_PATTERN, arg_list)]
        else:
            return []

    def get_kwargs(self) -> dict:
        """
        Return all keyword args with cast values as a dictionary.
        """
        kwarg_list_tag = AutonamePattern.get_single_tag('kwarg_list', self.match)
        if kwarg_list := self.match[kwarg_list_tag]:
            return dict(
                self._cast_kwarg_match(kw_pair) for kw_pair in
                re.finditer(
                    self.LITERAL_KWARG_PATTERN, kwarg_list))
        else:
            return {}


class Parser:
    """
    Parses a value string from a container and resolves all function calls.
    """

    _fxns = {}
    _lock = Lock()
    NS_VARNAME_PATTERN = re.compile(str(pxs.NS_VARNAME))

    @classmethod
    def register(cls, name: str, fxn: Callable, overwrite=False):
        """
        Register a function for interpretation by the parser. Functions can return string or non-string values. When functions are embedded in a string, their return value will be converted to a string before interpolation. When they span the entire string, their type will be preserved.
        """
        with cls._lock:
            if not overwrite and name in cls._fxns:
                raise Exception('Function name `{name}` already exists.')
            elif not re.fullmatch(cls.NS_VARNAME_PATTERN, name):
                raise Exception('Invalid function name `{name}`.')
            else:
                cls._fxns[name] = fxn

    def get_fxn(self, name):
        try:
            return self._fxns[name]
        except KeyError:
            raise KeyError(f'No registered function with name `{name}`.')

    def _replace(self, in_str, match: re.Match, repl_str):
        """
        Replaces the part of ``in_str`` that match was extracted from with ``match_val``.
        """
        match_len = (span := match.span())[1] - span[0]
        if match_len == len(in_str):
            # Match spans full input string, no casting to string.
            return repl_str
        else:
            return f'{in_str[:span[0]]}{repl_str}{in_str[span[1]:]}'

    def parse(self, val: str) -> Any:
        """
        Resolves nested functions in the input string. 

        The output is a string unless the entire string is a function call, in which case the type is determined by that call.

        If the output is a string
        """
        while isinstance(val, str) and (match := re.search(Function.FXN_PATTERN, val)):
            match_fxn = Function(match)
            match_val = self.get_fxn(
                match_fxn.name)(
                *match_fxn.get_args(),
                **match_fxn.get_kwargs())
            val = self._replace(val, match, match_val)

        return val
