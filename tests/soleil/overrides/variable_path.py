from contextlib import contextmanager
from functools import partial
from soleil.loader.loader import GLOBAL_LOADER, load_solconf
from soleil.overrides import variable_path as mdl
from soleil.resolvers.module_resolver import SolConfModule
from tests.helpers import solconf_package
from soleil.solconf import noid, hidden

package_with_header = partial(
    solconf_package,
    header="\n".join(
        [
            "from soleil.solconf import * ",
            "from soleil.overrides.variable_path import VarPath",
        ]
    ),
)


class TestVarPath:
    def test_no_prom(self):
        with package_with_header(
            {
                "main": """
a = load('sub1.sm1')
x:hidden = 1
""",
                "sub1.sm1": """
b = 1
c:noid = 2
""",
            }
        ) as path:
            ldm = load_solconf(path / "main.solconf", resolve=False)
            main = ldm
            sub1_sm1 = GLOBAL_LOADER.modules[".".join([ldm.__package__, "sub1.sm1"])]

            vp = mdl.VarPath.from_str("a")
            a, cx = vp.get_with_container(ldm)
            assert isinstance(a, SolConfModule)
            assert vp.get_modifiers(ldm) is None
            assert a.__soleil_var_path__.as_str() == "a"
            assert cx is main

            vp = mdl.VarPath.from_str("x")
            assert vp.get_modifiers(ldm) is hidden

            vp = mdl.VarPath.from_str("a.b")
            b, cx = vp.get_with_container(ldm)
            assert isinstance(b, int) and b == 1
            assert isinstance(cx, SolConfModule)
            assert vp.get_modifiers(ldm) is None
            assert cx.__soleil_var_path__.as_str() == "a"
            assert cx is sub1_sm1

            vp = mdl.VarPath.from_str("a.c")
            c, cx = vp.get_with_container(ldm)
            assert isinstance(c, int) and c == 2
            assert vp.get_modifiers(ldm) == noid
            assert cx is sub1_sm1

    def test_with_prom(self):
        with package_with_header(
            {
                "main": """

@promoted
class A:
    a = load('sub1.sm1')
""",
                "sub1.sm1": """
@promoted
class B:
    b = 1
    c:noid = 2
""",
            }
        ) as path:
            ldm = load_solconf(path / "main.solconf", resolve=False)
            main = GLOBAL_LOADER.modules[ldm.__module__]
            A = main.A
            sub1_sm1 = GLOBAL_LOADER.modules[".".join([main.__package__, "sub1.sm1"])]
            B = sub1_sm1.B

            vp = mdl.VarPath.from_str("a")
            a, cx = vp.get_with_container(ldm)
            assert a is B
            assert cx is A

            vp = mdl.VarPath.from_str("a.b")
            b, cx = vp.get_with_container(ldm)
            assert isinstance(b, int) and b == 1
            assert cx is B

            vp = mdl.VarPath.from_str("a.c")
            c, cx = vp.get_with_container(ldm)
            assert isinstance(c, int) and c == 2
            assert vp.get_modifiers(ldm) == noid
            assert cx is B
