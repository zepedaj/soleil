import rich


class _Unassigned:
    # TODO: Is this used somewhere?
    pass


def node_info_str(node):
    decorator_strs = []
    if node.types is not None:
        decorator_strs.append(f'types={node.types}')
    if node.modifiers != ():
        decorator_strs.append(f'modifiers={node.modifiers}')
    return f"{node}({', '.join(decorator_strs) if decorator_strs else ''})"


def print_tree(root, do_print=True, as_str=False):
    #
    from soleil.solconf.containers import Container

    #
    if do_print:
        fxn = str if as_str else rich.print
        return fxn(print_tree(root, False))

    #
    if isinstance(root, Container):
        return {node_info_str(root): [print_tree(child, False) for child in root.children]}
    else:
        return node_info_str(root)
