from soleil.loader.loader import load_solconf
from tests.helpers import solconf_package


class TestReq:
    def test_all(self):
        with solconf_package(
            {
                "main": """
a = load('submod', reqs=[{'b':2}])
""",
                "submod": """
b = req()
""",
            }
        ) as temp_dir:
            val = load_solconf(temp_dir / "main.solconf")
            assert val["a"]["b"] == 2

            val = load_solconf(temp_dir / "main.solconf", overrides=["a.b=3"])
            assert val["a"]["b"] == 3
