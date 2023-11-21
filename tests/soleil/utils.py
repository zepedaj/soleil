from soleil import utils as mdl
from soleil.resolvers.base import resolve
from tests import load_test_data


def test_overrides():
    assert resolve(
        actual2 := load_test_data(
            "utils/overrides/main",
            overrides=["symbol='Alpha'", "color='green'"],
            resolve=True,
        )
    ) == {
        "symbol": "Alpha",
        "color": "Green",
        "filename": "Alpha/color='green'.yaml",
    }

    #
    assert resolve(actual1 := load_test_data("utils/overrides/main")) == {
        "symbol": "Omega",
        "color": "Red",
        "filename": "Omega/default.yaml",
    }

    #


def test_id_str():
    raise Exception("Missing")
