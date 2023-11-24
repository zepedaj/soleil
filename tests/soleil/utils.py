from soleil import utils as mdl
from soleil import load_config
from soleil.resolvers.base import resolve
from tests import load_test_data
from tests.helpers import solconf_package


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
        "filename": "Alpha/main,color='green'.yaml",
    }

    #
    assert resolve(actual1 := load_test_data("utils/overrides/main")) == {
        "symbol": "Omega",
        "color": "Red",
        "filename": "Omega/main.yaml",
    }

    #


class TestIDStr:
    def test_base(self):
        with solconf_package(
            {
                "main": """
a = 1
id_str_0 = id_str()
b = load('.submod')
id_str_1 = id_str()
""",
                "submod": """
c:noid = 2
d = 3
""",
            }
        ) as root:
            #
            rslvd = load_config(root / "main.solconf")
            assert rslvd["id_str_0"] == rslvd["id_str_1"] == "main"

            #
            rslvd = load_config(root / "main.solconf", overrides=["a=2", "b.c=3;b.d=4"])
            assert rslvd["id_str_0"] == rslvd["id_str_1"] == "main,a=2,b.d=4"
