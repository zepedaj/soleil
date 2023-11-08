from soleil.resolvers import modifiers as mdl
import pytest, re


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
