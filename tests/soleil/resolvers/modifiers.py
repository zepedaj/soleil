from soleil.loader.loader import load_config
from soleil.resolvers import modifiers as mdl
import pytest, re

from tests.soleil.test_helpers import solconf_file


class TestModifiers:
    def test_all(self):
        assert mdl.Modifiers(hidden=True) == mdl.hidden
        assert mdl.Modifiers(hidden=False) == mdl.visible
        assert mdl.Modifiers(cast=int) == mdl.cast(int)
        assert mdl.Modifiers(name="myname") == mdl.name("myname")

    def test_merge(self):
        with pytest.raises(
            ValueError, match=re.escape("Multiply-specified modifier `hidden`")
        ):
            mdl.merge_modifiers(mdl.visible, mdl.hidden)

        assert mdl.merge_modifiers(
            mdl.visible, mdl.cast(int), mdl.name("myname")
        ) == mdl.Modifiers(hidden=False, cast=int, name="myname")

    def test_decorator(self):
        contents = """
@visible
class A:
    a = 1
"""
        with solconf_file(contents) as fl:
            mdl = load_config(fl, resolve=False)
            assert mdl.__annotations__["A"] == mdl.visible
            assert mdl.A.a == 1

    def test_decorator_tuple(self):
        contents = """
@hidden
@noid
class A:
    a = 1
"""
        with solconf_file(contents) as fl:
            mdl = load_config(fl, resolve=False)
            assert mdl.__annotations__["A"] == (mdl.noid, mdl.hidden)
            assert mdl.A.a == 1
