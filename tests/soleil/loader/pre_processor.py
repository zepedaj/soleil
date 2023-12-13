from dataclasses import dataclass
import re
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from soleil.loader import pre_processor as mdl
from itertools import chain
import ast
from soleil.loader.loader import load_config
from soleil.resolvers.base import resolve

from tests import load_test_data
from tests.helpers import solconf_file


def code_with_imports():
    return """
import os
import jztools.validation
from sys import *
class A:
    import os as Aos
"""


def code_with_assignments():
    return """
a = b
class C:
    d = f
"""


def code_with_calls():
    def fxn0(*args, **kwargs):
        pass

    globals().update({"a": 1, "b": 2, "fxn0": fxn0})
    return """
output = fxn0(a, b, c=3)
"""


@dataclass
class Ref:
    x: str


class ref_call:
    def __init__(self, call, *args, **kwargs):
        self.call = call
        self.args = args
        self.kwargs = kwargs

    def __eq__(self, x):
        return all(getattr(self, k) == getattr(x, k) for k in vars(self))


class TestGetImportedNames:
    def test_GetImportedNames(self):
        tree = (snv := mdl.GetImportedNames(None)).visit(ast.parse(code_with_imports()))

        import sys

        assert set(snv.imported_names) == set(
            chain(["jztools", "os", "Aos"], list(vars(sys)))
        )


class TestCLIROverrider:
    def test_all(self):
        assert resolve(load_test_data("pre_processor/overrides/main")) == {
            "a": 1,
            "b": 2,
            "c": 3,
        }

        assert resolve(
            load_test_data("pre_processor/overrides/main", overrides=["a=2"])
        ) == {
            "a": 2,
            "b": 3,
            "c": 4,
        }

    def test_nested_cli_overrides(self):
        # No override
        module = resolve(load_test_data("solconf_module_tests/nested_overrides/main"))
        assert module == {"country": "Nicaragua", "city": "Managua"}

        # One override
        module = resolve(
            load_test_data(
                "solconf_module_tests/nested_overrides/main",
                overrides=[
                    "country='france'",
                    # "place.city='nantes'",
                ],
            ),
        )
        assert module == {"country": "France", "city": "Paris"}

        # One override, nested
        module = resolve(
            load_test_data(
                "solconf_module_tests/nested_overrides/main",
                overrides=[
                    "country.city='chinandega'",
                ],
            ),
        )
        assert module == {"country": "Nicaragua", "city": "Chinandega"}

        # Two overrides on same line
        module = resolve(
            load_test_data(
                "solconf_module_tests/nested_overrides/main",
                overrides=[
                    "country='france'",
                    "country.city='nantes'",
                ],
            ),
        )
        assert module == {"country": "France", "city": "Nantes"}

    # TODO: Make the following two tests work
    #
    # def test_overrides_of_non_loaded(self):
    #     # No override
    #     module = resolve(
    #         load_test_data(
    #             "solconf_module_tests/nested_overrides/non_loaded",
    #             overrides=["A.b=A.a"],
    #         )
    #     )
    #     assert module.a == module.b == 1

    # def test_overrides_with_subscripts(self):
    #     module = load_test_data(
    #         "solconf_module_tests/nested_overrides/main",
    #         overrides=["country.country[0]='X'"],
    #     )
    #     assert module == {"country": "Xicaragua", "city": "Managua"}


class TestProtectKeyword:
    def test_keywords_protected(self):
        with TemporaryDirectory() as temp_dir:
            for keyword in mdl.__soleil_keywords__:
                with open(path := (Path(temp_dir) / "main.solconf"), "w") as fo:
                    fo.write(f"{keyword} = 1")

                with pytest.raises(
                    SyntaxError,
                    match=re.escape(
                        f'Attempted to redefine soleil keyword `{keyword}` - File "{path}", line 1'
                    ),
                ):
                    load_config(path)


class TestGetPromotedName:
    def test_double_promoted_fails(self):
        with solconf_file("A:promoted\nB:promoted") as path:
            with pytest.raises(
                SyntaxError,
                match=re.escape('Multiple promotions detected ("A", "B") - File "')
                + ".*"
                + re.escape('main.solconf", line 3'),
            ):
                load_config(path)

    def test_non_root_promoted_fails(self):
        with solconf_file("class A:\n\ta:promoted=1") as path:
            with pytest.raises(
                SyntaxError,
                match=re.escape(
                    f'Attempted to promote non-root member `A.a` - File "{path}", line 3'
                ),
            ):
                load_config(path)

    def test_non_root_promoted_fails__decorator(self):
        with solconf_file("class A:\n\ta:promoted=1") as path:
            with pytest.raises(
                SyntaxError,
                match=re.escape(
                    f'Attempted to promote non-root member `A.a` - File "{path}", line 3'
                ),
            ):
                load_config(path)
