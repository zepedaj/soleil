from uuid import uuid4
from soleil.loader import GLOBAL_LOADER
from tests import TEST_DATA_ROOT, load_test_data
from soleil import resolve
from soleil.resolvers.base import displayable


class TestSolConfModule:
    def test_load(self):
        mdl = load_test_data("solconf_module_tests/main", resolve=False)
        assert (
            load_test_data("solconf_module_tests/main", resolve=True)["red"] == "redish"
        )
        assert resolve(load_test_data("solconf_module_tests/main").red) == "redish"

    def test_submodule(self):
        # No overrides
        module = load_test_data("solconf_module_tests/main", package_name=uuid4().hex)
        assert resolve(module)["red"] == "redish"
        assert resolve(module.red) == "redish"
        assert resolve(module)["chosen_color"] == "blueish"
        assert resolve(module.chosen_color) == "blueish"

        # With overrides
        module = load_test_data(
            "solconf_module_tests/main",
            package_name=uuid4().hex,
            overrides=["chosen_color='green'"],
        )
        assert resolve(module)["red"] == "redish"
        assert resolve(module.red) == "redish"
        assert resolve(module)["chosen_color"] == "greenish"
        assert resolve(module.chosen_color) == "greenish"

    def test_reqs(self):
        loader = ConfigLoader(TEST_DATA_ROOT, name := random_name())

        assert loader.load(
            f"{name}.solconf_module_tests.reqs", resolve=True, reqs={"a": 1, "b": 2}
        ) == {"a": 1, "b": 2, "c": 3}

    def test_promoted_getitem(self):
        module = load_test_data("solconf_module_tests/subscripting", resolve=False)
        assert module[0] == "a"
        assert module[3] == "d"

    def test_displayable(self):
        module = load_test_data("solconf_module_tests/main", package_name=uuid4().hex)
        out = displayable(module)
        assert out == {
            "red:{'promoted': False}": {"color": "redish"},
            "chosen_color": {"color": "blueish"},
        }

    def test_derive(self):
        module = load_test_data(
            "solconf_module_tests/main", package_name=uuid4().hex, resolve=False
        )

        assert isinstance(module, type)

        class derived_module(module):
            red = "orange"

        assert module in derived_module.mro()

        out1 = resolve(module)
        out2 = resolve(derived_module)

        assert out1 is not out2
        assert out1 == {"chosen_color": "blueish", "red": "redish"}
        assert out2 == {"chosen_color": "blueish", "red": "orange"}
