from uuid import uuid4
import pytest
from soleil.loader import GLOBAL_LOADER
from soleil.loader.loader import load_config
from tests import TEST_DATA_ROOT, load_test_data
from soleil import resolve
from soleil.resolvers.base import displayable
from tests.helpers import solconf_file, solconf_package


class TestSolConfModule:
    def test_load(self):
        mdl = load_test_data("solconf_module_tests/main", resolve=False)
        assert (
            load_test_data("solconf_module_tests/main", resolve=True)["red"]
            == "reddish"
        )
        assert resolve(load_test_data("solconf_module_tests/main").red) == "reddish"

    def test_submodule(self):
        # No overrides
        module = load_test_data("solconf_module_tests/main", package_name=uuid4().hex)
        assert resolve(module)["red"] == "reddish"
        assert resolve(module.red) == "reddish"
        assert resolve(module)["chosen_color"] == "blueish"
        assert resolve(module.chosen_color) == "blueish"

        # With overrides
        module = load_test_data(
            "solconf_module_tests/main",
            package_name=uuid4().hex,
            overrides=["chosen_color='green'"],
        )
        assert resolve(module)["red"] == "reddish"
        assert resolve(module.red) == "reddish"
        assert resolve(module)["chosen_color"] == "greenish"
        assert resolve(module.chosen_color) == "greenish"

    def test_reqs(self):
        loader = GLOBAL_LOADER
        loader.init_package(
            TEST_DATA_ROOT, name := uuid4().hex, overrides=[{"a": 1, "b": 2}]
        )

        assert loader.load(f"{name}.solconf_module_tests.reqs", resolve=True) == {
            "a": 1,
            "b": 2,
            "c": 3,
        }

    def test_promoted_getitem(self):
        module = load_test_data("solconf_module_tests/subscripting", resolve=False)
        assert module[0] == "a"
        assert module[3] == "d"

    def test_displayable(self):
        module = load_test_data("solconf_module_tests/main", package_name=uuid4().hex)
        out = displayable(module)
        assert out == {
            "red:{'promoted': False}": {"color": "reddish"},
            "chosen_color": {"color": "blueish"},
        }

    def test_derive(self):
        B = load_test_data("solconf_module_tests/derivation/derived", resolve=False)
        assert [x.__name__ for x in B.mro()] == ["B", "A", "object"]
        assert resolve(B) == {"a": 1, "b": 2, "c": 3, "d": 4}

        B = load_test_data(
            "solconf_module_tests/derivation/derived", resolve=False, overrides=["a=10"]
        )
        assert [x.__name__ for x in B.mro()] == ["B", "A", "object"]
        assert resolve(B) == {"a": 10, "b": 11, "c": 12, "d": 13}

    def test_overrides(self):
        assert load_test_data("overrides/main", resolve=True) == {
            "a": 1,
            "b": 2,
            "c": 3,
        }

        assert load_test_data("overrides/main", resolve=True, overrides=[{"a": 2}]) == {
            "a": 2,
            "b": 3,
            "c": 4,
        }

        assert load_test_data("overrides/main", resolve=True, overrides=["a=2"]) == {
            "a": 2,
            "b": 3,
            "c": 4,
        }

    def test_overrides_nested_promote(self):
        assert load_test_data("overrides/nested_promote/main", resolve=True) == {
            "a": 0.5,
            "b": 1.5,
        }

        assert load_test_data(
            "overrides/nested_promote/main", resolve=True, overrides=["a=3"]
        ) == {"a": 3, "b": 4}

    def test_single_promoted(self):
        with solconf_file(
            """
from soleil import *
A:resolves = 1
B:promoted = 2
"""
        ) as fl:
            with pytest.raises(
                ValueError,
                match="Solconf modules cannot have both `promoted` and `resolves` members",
            ):
                resolve(load_config(fl))
