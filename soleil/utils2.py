class _Unassigned:
    pass


class Namespace:
    """
    Namespaces define classes whose attributes can be accessed from configuration strings using dot notation.

    Namespace classes should not be instantiated.
    """

    name: str  # Namespace name for this class accessible from the parser context.

    def __new__(cls, *args, **kwargs):
        raise Exception('Namespace classes should not be instantiated!')

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
