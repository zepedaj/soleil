from jztools.reference_sequence import RefSeq, base_get, base_set, getter, setter
from soleil.resolvers.base import TypeResolver, resolve


class resolved(RefSeq):
    """
    Returns an object that will resolve to the resolution of the input resolvable but
    that can be accessed (i.e., attributes and subscripts accessed) as if the object
    were already resolved. Note that each reference will return a new
    resolvable of type :class:`resolved` and not the actual attribute or entry.

    .. code-block::

        class fl:
            type:as_type = file
            args:as_args = ('/tmp/my_file',)

        mode = resolved(fl).mode
    """

    __ref_seq_protected__ = ("__soleil_resolved__", "__class__", "__dict__")

    def __init__(self, resolvable):
        self.resolvable = resolvable
        super().__init__()

    @classmethod
    def copy(cls, obj, *args, **kwargs):
        return super().copy(obj, *args, **kwargs, out=cls(base_get(obj, "resolvable")))


class ResolvedResolver(TypeResolver, handled_type=resolved):
    def compute_resolved(self):
        resolvable = base_get(self.resolvable, "resolvable")

        # Resolve the resolvable
        resolved = resolve(resolvable)
        # Dereference the resolvable and return
        return getter(self.resolvable, resolved)
