from soleil.resolvers import class_resolver as mdl
from soleil.injected import *
from soleil.resolvers.modifiers import merge_modifiers


class Resolvable1:
    type: as_type = lambda **kwargs: list(sorted(kwargs.values()))
    val1 = 1
    val2 = 2
    val3 = 3
    __excluded__ = 4


class Resolvable2(Resolvable1):
    __val4__ = 4


class Resolvable3(Resolvable2):
    __val4__: (visible, cast(lambda x: x))


class ResolvableFancyType:
    type: (visible, as_type, name("unused")) = lambda **kwargs: dict(kwargs)
    val1 = 1
    val2 = 2
    val3 = 3


class VariableArgs:
    type: as_type = lambda *args: args
    x: as_args = (1, 2, 3, 4)


class TestClassResolver:
    def test_all(self):
        assert not mdl.ClassResolver.can_handle(TestClassResolver)
        assert mdl.ClassResolver.can_handle(Resolvable1)

        assert (x1 := mdl.resolve(Resolvable1)) == [1, 2, 3]

        assert "__val4__" not in mdl.ClassResolver(Resolvable2).members
        assert (x2 := mdl.resolve(Resolvable2)) == [1, 2, 3]
        assert not mdl.ClassResolver(Resolvable3).modifiers["__val4__"]["hidden"]
        assert (x3 := mdl.resolve(Resolvable3)) == [1, 2, 3, 4]

        r_ = lambda x: mdl.resolve(x)
        assert (
            x1
            is r_(Resolvable1)
            is not x2
            is r_(Resolvable2)
            is not x3
            is r_(Resolvable3)
        )

    def test_fancy_as_type(self):
        assert merge_modifiers(*ResolvableFancyType.__annotations__["type"])["as_type"]
        assert mdl.ClassResolver.can_handle(ResolvableFancyType)
        assert resolve(ResolvableFancyType) == {"val1": 1, "val2": 2, "val3": 3}

    def test_variable_args(self):
        x = resolve(VariableArgs)
        assert x == (1, 2, 3, 4)
