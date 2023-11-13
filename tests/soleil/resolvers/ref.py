from soleil.resolvers import ref as mdl
from tests import load_test_data


class TestRef:
    def test_all(self):
        x = load_test_data("ref/ref", resolve=True)
        assert (
            1
            == x["r"]
            == x["x"]
            == x["A"]["r"]
            == x["A"]["x"]
            == x["A"]["B"]["r"]
            == x["A"]["B"]["x"]
        )
        assert x["A"]["a"] == x["A"]["y"] == 2
        assert x["A"]["B"]["b"] == x["A"]["B"]["z"] == 3


class TestCall:
    def test_all(self):
        x = load_test_data("ref/fxn_resolution", resolve=True)
        breakpoint()
        pass
