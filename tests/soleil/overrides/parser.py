#
from soleil.overrides import parser as mdl

S = mdl.Subscript
A = mdl.Attribute


class TestRefExtractor:
    def test_all(self):
        for ref, expected in [
            ("a", [A("a")]),
            ("a.b[0].c", [A("a"), A("b"), S(0), A("c")]),
            ("a['abc']", [A("a"), S("abc")]),
        ]:
            assert mdl.parse_ref(ref) == expected


class TestOverrideSplitter:
    ovr_strs = [
        ("a.b=2", [A("a"), A("b")], mdl.OverrideType.existing, 2),
        (
            "a[0].b=5*2+2**2/2",
            [A("a"), S(0), A("b")],
            mdl.OverrideType.existing,
            12,
        ),
    ]

    def test_single(self):
        for ovr_str, target, ovr_type, value in self.ovr_strs:
            overrides = mdl.parse_overrides(ovr_str)
            assert len(overrides) == 1
            ovr = overrides[0]
            assert ovr.get_value() == value
            assert ovr.target == target
            assert ovr.assign_type is ovr_type

    def test_multi(self):
        k = None
        ovr_multi_str = "\n".join(x[0] for x in self.ovr_strs)

        for k, ((_, target, ovr_type, value), ovr) in enumerate(
            zip(self.ovr_strs, mdl.parse_overrides(ovr_multi_str))
        ):
            assert ovr.get_value() == value
            assert ovr.target == target
            assert ovr.assign_type is ovr_type

        assert k == len(self.ovr_strs) - 1
