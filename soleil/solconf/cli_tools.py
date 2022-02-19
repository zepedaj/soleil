from typing import List, Optional
from .modification_heuristics import modify_ref_path
import yaml
from .exceptions import InvalidOverridePattern
import re
from soleil.solconf.nodes import Node
from soleil.solconf.solconf import SolConf


class SolConfArg:
    """
    Can be passed as a value for ``type`` when defining a Python argparse argument:

    .. doctest:: SolConfArg

      >>> import argparse
      >>> from soleil import SolConfArg

      >>> parser = argparse.ArgumentParser()
      >>> parser.add_argument('arg', nargs='*', type=SolConfArg())
      _StoreAction(option_strings=[], dest='arg', nargs='*', const=None, default=None, type=<soleil.solconf.cli_tools.SolConfArg object at 0x...>, choices=None, help=None, metavar=None)

    """

    _OVERRIDE_PATTERN = re.compile(
        f'(?P<ref_str>{Node._FULL_REF_STR_PATTERN_RAW})(?P<assignment_type>\\=|\\*\\=)(?P<raw_content>.*)')

    def __init__(self, config_source: str = None):
        """
        .. doctest:: SolConfArg

          >>> sca1 = SolConfArg() # or SolConfArg
          >>> config = sca1(['yaml/load_with_choices/config.yaml', "typing_a=c++", "typing_b=c++"]) # Path required
          >>> sca2 = SolConfArg('yaml/load_with_choices/config.yaml')
          >>> config = sca2(["typing_a=c++", "typing_b=c++"]) # Path optional?

        In the case where a path is specified in the initializer, it can still be overriden using a root clobber assignment:

        .. doctest:: SolConfArg

          >>> config = sca2(['.*={"_::load,promote": yaml/colors/colors_config.yaml}'])

        One disadvantage of this approach is that the original ``config_source`` will still be loaded before the clobber assignment is carried out. The **root clober**  special syntax ``**=<path>`` has the same effect but avoids this drawback:

        .. doctest:: SolConfArg

          >>> # config = sca2(['**=source/content/yaml/colors/colors_config.yaml'])

        """
        self.config_source = config_source

    def __call__(self,  overrides: Optional[List[str]] = None):
        """
        If the object was initialized without specifying a ``config_source``, then the first entry of ``overrides`` must contain it.

        .. rubric:: Workflow:

        1) Load the configuration file specified by ``config_source`` to create a :class:`SolConf` object. Do not apply modifiers during :class:`SolConf` initialization..
        2) For each override:

          1) For consistency with :class:`SolConf.load` any input value is first loaded using ``yaml.safe_load`` -- this does some interpretation. For example strings that represent integers, booleans or null are converted to an integer, boolean and ``None``, respectively. The resulting value is the **raw content**.
          2) Apply all modifiers of the path implicit in the reference string (except for the last component) using :func:`~modification_heuristics.modify_ref_path`. This enables e..g, modifying ``load`` targets. Because of this application of modifiers, the order in which overrides are provided is important.
          3) Assign the override value depending on the assignment type:

            * **Value assignment (=)**: Valid if the target is a :class:`~soleil.solconf.nodes.ParsedNode` (or rather, if it exposes a :attr:`~soleil.solconf.nodes.ParsedNode.raw_value` attribute), in which case it replaces the :attr:`~soleil.solconf.nodes.ParsedNode.raw_value` of the :class:`~soleil.solconf.nodes.ParsedNode` with the new value.
            * **Clobber assignment (*=)**: Create a new node (or node sub-tree) from the provided raw content. Discard the target node, if any, and add the new node.

        """

        overrides = overrides or []

        # If config file not previously defined, get from overrides
        if self.config_source is None:
            self.config_source = overrides.pop(0)

        # Load config file, do not apply modifiers yet.
        sc = SolConf.load(self.config_source, modify=False)

        # Alter the loaded node tree with the specified overrides.
        for ref_str, assignment_type, raw_content_str in map(self._parse_override_str, overrides):

            #
            raw_content = yaml.safe_load(raw_content_str)

            # Modify all nodes in the specified path.
            # This is required to e.g., apply load target overrides or load content that the
            # reference string refers to.
            components = Node._get_ref_components(ref_str)
            if len(components) > 1:
                modify_ref_path(sc.root, components[:-1])

            # Get node
            node = sc.root
            for _component in components:
                node = node._node_from_ref_component(_component)

            # Apply assignment
            if assignment_type == '=':
                # Value assignment

                # Rather than checking if type is ParsedNode, check for the attribute.
                if hasattr(node, 'raw_value'):
                    node.raw_value = raw_content
                else:
                    raise TypeError(f'Cannot assign to node {node}.')

            elif assignment_type == '*=':
                # Clobber assignment

                # Build the new node sub-tree, force eval of raw content.
                new_node = SolConf.build_node_tree(raw_content, parser=sc.parser)

                # Replace the new node as the value in the original KeyNode.
                node = sc.root.node_from_ref(ref_str)
                (node.parent if node.parent else node.sol_conf_obj).replace(node, new_node)

        # Modify all remaining non-modified parts.
        sc.modify_tree()

        # Resolve the tree
        return sc()

    @classmethod
    def _parse_override_str(cls, override: str):
        """
        Parses the override string, extracting 1) the qualified name of the target, 2) the assignment type and 3) the yaml-parsed raw content.
        """
        if not (parts := re.fullmatch(cls._OVERRIDE_PATTERN, override)):
            raise InvalidOverridePattern(override)
        else:
            return parts['ref_str'], parts['assignment_type'], parts['raw_content']
