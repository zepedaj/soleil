from soleil import resolve
from tests import load_test_data


class TestBaseResolvers:
    def test_all(self):
        loaded = load_test_data("base_resolvers")
        resolve(loaded)
