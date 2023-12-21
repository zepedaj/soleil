import pytest
from soleil import utils as mdl
from soleil import load_solconf
from soleil.loader.loader import UnusedOverrides
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
    def test_base_full(self):
        with solconf_package(
            {
                "main": """
a = 1
id_str_0 = id_str(full=True)
b = load('.submod')
id_str_1 = id_str(full=True)
""",
                "submod": """
c:noid = 2
d = 3
""",
            }
        ) as root:
            #
            rslvd = load_solconf(root / "main.solconf")
            assert rslvd["id_str_0"] == rslvd["id_str_1"] == "main"

            #
            rslvd = load_solconf(
                root / "main.solconf", overrides=["a=2", "b.c=3;b.d=4"]
            )
            assert rslvd["id_str_0"] == rslvd["id_str_1"] == "main,a=2,b.d=4"

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
            rslvd = load_solconf(root / "main.solconf")
            assert rslvd["id_str_0"] == rslvd["id_str_1"] == "main"

            #
            rslvd = load_solconf(
                root / "main.solconf", overrides=["a=2", "b.c=3;b.d=4"]
            )
            assert rslvd["id_str_0"] == rslvd["id_str_1"] == "main,a=2,d=4"

    def test_spawn(self):
        with solconf_package(
            {
                "main": """
@promoted
class _:
    type: as_type = lambda **kwargs: kwargs
    a=1
    b=2
    c=3   
""",
                "main2": """
@promoted
class _(spawn('.main')):
    d=4
""",
                "main3": """
@promoted
class _(spawn('.main', default_overrides=[{'b':20}])):
    d=4
""",
                "fails": """
@promoted
class _(spawn('.main', default_overrides=[{'x':20}])):
    d=4
""",
            }
        ) as root:
            rslvd = load_solconf(root / "main2.solconf")
            assert rslvd == {"a": 1, "b": 2, "c": 3, "d": 4}

            rslvd = load_solconf(root / "main2.solconf", overrides=["a=10"])
            assert rslvd == {"a": 10, "b": 2, "c": 3, "d": 4}

            rslvd = load_solconf(root / "main3.solconf")
            assert rslvd == {"a": 1, "b": 20, "c": 3, "d": 4}

            rslvd = load_solconf(root / "main3.solconf", overrides=["a=10; b=200"])
            assert rslvd == {"a": 10, "b": 200, "c": 3, "d": 4}

            with pytest.raises(
                UnusedOverrides, match=r"Unused spawn default override\(s\) x"
            ):
                rslvd = load_solconf(root / "fails.solconf")
