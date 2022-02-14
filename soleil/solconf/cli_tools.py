from typing import List
from .exceptions import InvalidOverridePattern
import re
from soleil.solconf.nodes import Node
from soleil.solconf.solconf import SolConf


class SolConfArg:
    """
    Can be passed as a value for ``type`` when defining a Python argparse argument:

    .. testcode::

      >>> import argparse
      >>> from soleil import SolConfArg

      >>> parser = argparse.ArgumentParser()
      >>> parser.add_argument('arg', nargs='*', type=SolConfArg())


    """

    _OVERRIDE_PATTERN = re.compile(
        f'(?P<qual_name>{Node._FULL_REF_STR_PATTERN_RAW})\\=(?P<raw_content>.*)')

    def __init__(self, config_source: str = None):
        """
        .. testcode::

          >> sc1 = SolConfArg() # or SolConfArg
          >> config = sc1(["'typing_a='c++'", "typing_b='c++'"])
          >> sc2 = SolConfArg('yaml/load_with_choices/config.yaml')
          >> config = SolConfArg('yaml/load_with_choices/config.yaml')(["'typing_a='c++'", "typing_b='c++'"])
        """
        self.config_source = config_source

    def __call__(self,  overrides: List[str] = None):
        """
        If the object was initialized without specifying a ``config_source``, then the first entry of ``overrides`` must contain it.
        """

        # If config file not previously defined, get from overrides
        if self.config_source is None:
            self.config_source = overrides.pop(0)

        # Load config file
        sc = SolConf.load(self.config_source)

        # Modify the loaded node tree with the specified new nodes
        for qual_name, raw_content in map(self._parse_override_str, overrides):

            # Build the new node sub-tree, force eval of raw content.
            new_node = SolConf.build_node_tree('$:'+raw_content, parser=sc.parser)

            # Replace the new node as the value in the original KeyNode.
            # Support for replacing the whole node tree could be added with
            #     node = node if (node := sc(qual_name)).parent else sc
            node = sc.root.node_from_ref(qual_name)
            node.parent.replace(node, new_node)

            # Modify the new node sub-tree
            if hasattr(new_node, 'modify'):
                new_node.modify()

        # Resolve the tree
        return sc()

    @classmethod
    def _parse_override_str(cls, override: str):
        if not (parts := re.fullmatch(cls._OVERRIDE_PATTERN, override)):
            raise InvalidOverridePattern(override)
        else:
            return parts['qual_name'], parts['raw_content']
