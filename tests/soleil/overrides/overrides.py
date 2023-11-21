from tests import load_test_data
from soleil.overrides.variable_path import VarPath


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
