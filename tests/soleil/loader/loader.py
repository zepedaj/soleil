import ast
from soleil.loader import loader as mdl
from soleil.resolvers.base import resolve
from tests import TEST_DATA_ROOT


class TestConfigLoader:
    def load(self, sub_path, resolve=False):
        return mdl.load_config(
            (TEST_DATA_ROOT / sub_path).with_suffix(".solconf"), resolve=resolve
        )

    def test_with_custom_type(self):
        module = self.load("loader/with_custom_type")
        assert resolve(module) == 1

    def test_with_promotion(self):
        module = self.load("loader/with_promotion")
        assert resolve(module) == 1

    def test_with_no_promotion(self):
        module = self.load("loader/with_no_promotion")
        assert resolve(module) == {"a": 1, "b": 2}

    def test_with_explicit_unpromotion(self):
        module = self.load("loader/with_explicit_unpromotion")
        assert resolve(module) == {"a": 1}

    def test_load_submodule(self):
        x = self.load("loader/with_submodules/main", resolve=True)
        assert x == "solid_black"
