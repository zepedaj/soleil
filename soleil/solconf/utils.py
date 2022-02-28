import rich


class _Unassigned:
    # TODO: Is this used somewhere?
    pass


def node_info_str(node):
    return f'{node}(types={node.types}, modifiers={node.modifiers})'


def print_tree(root, do_print=True):
    #
    from soleil.solconf.containers import Container

    #
    if do_print:
        rich.print(print_tree(root, False))
        return
    #
    if isinstance(root, Container):
        return {node_info_str(root): [print_tree(child, False) for child in root.children]}
    else:
        return node_info_str(root)
