from tests import load_test_data
import re
import pytest
from soleil.overrides.variable_path import VarPath
from soleil.overrides import overrides as mdl


class TestOverrides:
    def test_soleil_var_path(self):
        mdl = load_test_data("overrides/main", resolve=False)
        assert not mdl.__soleil_var_path__

        mdl = load_test_data("overrides/nested/main", resolve=False)
        assert not mdl.__soleil_var_path__
        assert mdl.m.__soleil_var_path__ == VarPath.from_str("m")
        assert mdl.m.m.__soleil_var_path__ == VarPath.from_str("m.m")

    def test_override(self):
        # assert load_test_data("overrides/main", resolve=True) == {
        #     "a": 1,
        #     "b": 2,
        #     "c": 3,
        # }

        assert load_test_data("overrides/main", resolve=True, overrides=["a=2"]) == {
            "a": 2,
            "b": 3,
            "c": 4,
        }

    def test_nested_override(self):
        assert load_test_data("overrides/nested/main", resolve=True) == {
            "a": 1,
            "b": 2,
            "m": {"c": 3, "d": 4, "m": {"e": 5, "f": 6, "g": 7}},
        }

        assert (
            load_test_data("overrides/nested/main", resolve=True, overrides=["a=2"])
        ) == {
            "a": 2,
            "b": 3,
            "m": {"c": 3, "d": 4, "m": {"e": 5, "f": 6, "g": 7}},
        }

        assert (
            load_test_data("overrides/nested/main", resolve=True, overrides=["m.c=4"])
        ) == {
            "a": 1,
            "b": 2,
            "m": {"c": 4, "d": 5, "m": {"e": 5, "f": 6, "g": 7}},
        }

    def test_multi_override(self):
        assert (
            load_test_data(
                "overrides/nested/main",
                resolve=True,
                overrides=["a=2", "m.c=4", "m.m.g=8"],
            )
        ) == {
            "a": 2,
            "b": 3,
            "m": {"c": 4, "d": 5, "m": {"e": 5, "f": 6, "g": 8}},
        }

    def test_classes(self):
        assert (x := load_test_data("overrides/nested/main2", resolve=True)) == {
            "A": {
                "a": 1,
                "b": 2,
                "m": {"B": {"c": 3, "d": 4, "m": {"C": {"e": 5, "f": 6, "g": 7}}}},
            }
        }

        assert (
            x := load_test_data(
                "overrides/nested/main2",
                resolve=True,
                overrides=["A.a=2", "A.m.B.c=4", "A.m.B.m.C.g='8'"],
            )
        ) == {
            "A": {
                "a": 2,
                "b": 3,
                "m": {"B": {"c": 4, "d": 5, "m": {"C": {"e": 5, "f": 6, "g": "8"}}}},
            }
        }

    def test_overload(self):
        assert (x := load_test_data("overrides/nested/main3", resolve=True)) == {
            "a": 1,
            "b": 2,
            "m": {"c": 3, "d": 4},
        }

        assert (
            x := load_test_data(
                "overrides/nested/main3", resolve=True, overrides=["a=1", "m.c=4"]
            )
        ) == {
            "a": 1,
            "b": 2,
            "m": {"c": 4, "d": 5},
        }


class TestFxns:
    def test_multiply_defined(self):
        with pytest.raises(
            ValueError, match=re.escape("Multiple overrides provided for target(s) `a`")
        ):
            mdl.eval_overrides(["a=2", "a=3"], {}, {})

        with pytest.raises(
            ValueError,
            match=re.escape("Multiple overrides provided for target(s) `a.x.y`"),
        ):
            mdl.eval_overrides(["a.x.y=2", "a.z.b=3", {"a.x.y": 5}], {}, {})

    def test_merge(self):
        os1 = mdl.eval_overrides(["a=1", "b=2"])
        os2 = mdl.eval_overrides(["c=1", "b=3"])

        mos = mdl.merge_overrides(os1, os2)

        assert {x.source for x in mos} == {"a=1", "b=3", "c=1"}
