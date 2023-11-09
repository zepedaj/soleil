from soleil import _utils as mdl
import pytest


def test_abs_mod_name():
    assert mdl.abs_mod_name("abc.def", ".xyz") == "abc.xyz"
    assert mdl.abs_mod_name("abc.def", "xyz") == "xyz"
    assert mdl.abs_mod_name("abc.def..ghi", ".xyz") == "abc.xyz"

    with pytest.raises(
        ValueError,
        match=f"Module reference `abc.def...xyz` refers beyond the root package",
    ):
        mdl.abs_mod_name("abc.def", "..xyz")
