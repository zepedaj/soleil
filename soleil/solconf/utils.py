import rich
from itertools import chain


class _Unassigned:
    # TODO: Is this used somewhere?
    pass


def kw_only(name):
    """
    Provides kw-only functionality for versions ``dataclasses.field`` that do not support it.

    .. TODO:: Use dataclass's ``kw_only`` support (`https://stackoverflow.com/a/49911616`).
    """

    def kw_only():
        raise Exception(f"Required keyword `{name}` missing")

    return kw_only


def node_info_str(node):
    decorator_strs = []
    if node.types is not None:
        decorator_strs.append(f"types={node.types}")
    if node.modifiers != ():
        decorator_strs.append(f"modifiers={node.modifiers}")
    return f"{node}({', '.join(decorator_strs) if decorator_strs else ''})"


def traverse_tree(root):
    """
    Iterates top-down, depth-first over all nodes in a tree. No nodes are modified during traversal.
    """
    #
    from soleil.solconf.containers import Container

    if isinstance(root, Container):
        yield root
        yield from chain(*[traverse_tree(child) for child in root.children])
    else:
        yield root


def print_tree(root, do_print=True, as_str=False):
    #
    from soleil.solconf.containers import Container

    #
    if do_print:
        fxn = str if as_str else rich.print
        return fxn(print_tree(root, False))

    #
    if isinstance(root, Container):
        return {
            node_info_str(root): [print_tree(child, False) for child in root.children]
        }
    else:
        return node_info_str(root)
