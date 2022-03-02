from typing import List, Optional
import yaml
import re
from soleil.solconf.modification_heuristics import modify_ref_path
from soleil.solconf.exceptions import InvalidOverridePattern
from soleil.solconf.nodes import Node
from soleil.solconf.solconf import SolConf
from ._argparse_patches import ReduceAction


class SolConfArg:
    """
    Enables |SolConf| arguments in |argparse| CLIs.

    Instances of this object can be passed as a value for the ``type`` keyword argument when calling :meth:`argparse.ArgumentParser.add_argument` (see the  |argparse| documentation). Assuming no :ref:`overrides <CLI overrides>` are specified, doing so will set the parsed value of that argument to

    .. code-block::

      SolConf.load(config_source)

    .. rubric:: Number of consumed CLI arguments

    If  ``config_source`` is not provided at |SolConfArg| initialization, the first CLI argument will be used in its place. Accordingly CLI arguments of type |SolConfArg| will by default consume 

      * one-or-more CLI arguments when ``config_source`` is not provided, or 
      * zero-or-more CLI arguments when ``config_source`` is provided. 

    This is done by internally setting the default keyword arguments ``nargs='+'`` or ``nargs='*'``, respectively, in the :meth:`argparse.ArgumentParser.add_argument` call. Users can override this behavior, e.g., by using ``nargs=1`` or ``nargs=0``, respectively.

    Any extra CLI arguments besides ``config_source`` are treated as :ref:`CLI overrides` that change the value of the loaded |SolConf| object.

    .. note::  

      An |argparse| argument of type |SolConfArg| will by default consume an unbounded number of CLI arguments. Hence, it must either be the only argument added to the :class:`ArgumentParser` object, or an optional argument.

    .. note::

      Even when :class:`SolConfArg` is instantiated with a ``config_source`` argument, the value of ``config_source`` can be overriden from the command line using a :ref:`source clobber <source clobber>` override.

    .. _CLI overrides:

    .. rubric:: CLI overrides

    Extra CLI arguments passed to an |argparse| argument of type |SolConfArg| specify overrides that change the values in the loaded |SolConf| object. Override specifiers can be of three types:

        * **Value assignment (=)**: Valid if the target is a :class:`~soleil.solconf.nodes.ParsedNode`, in which case the assignment replaces the :attr:`~soleil.solconf.nodes.ParsedNode.raw_value` of the :class:`~soleil.solconf.nodes.ParsedNode` with the new value. This new value can be a literal or |dstring|.
        * **Clobber assignment (*=)**: Create a new node (or node sub-tree) from the provided raw content. The target node, if any, is discarded, and the new node added.
        * **Source clobber (**=)**: Sets or replaces the ``config_source`` argument of the ``SolConfArg`` object. See :ref:`below <source clobber>`.


    .. todo:: This class and |extends| share a lot of common functionality. Is it possible to merge the two?

    """

    _OVERRIDE_PATTERN = re.compile(
        f'(?P<ref_str>{Node._FULL_REF_STR_PATTERN_RAW})(?P<assignment_type>\\=|\\*\\=)(?P<raw_content>.*)')

    def __init__(self, config_source: str = None):
        """

        .. testsetup:: SolConfArg

          import conf
          from pathlib import Path
          examples_root = str(Path(conf.__file__).parent / 'content') + '/'  # Necessary bc CWD changes between `make doctest` runs.
          from soleil import SolConfArg
          from rich import print

        .. doctest:: SolConfArg

          # Option 1: Path must be provided with argparse arguments
          >>> sca1 = SolConfArg()          
          >>> sca1([f'{examples_root}/yaml/load_with_choices/config.yaml', "typing_a=c++", "typing_b=c++"])
          {'typing_a': 'hard', 'typing_b': 'hard', 'typing_c': 'hard'}

          # Option 2: Path provided with argument definition
          >>> sca2 = SolConfArg(f'{examples_root}/yaml/load_with_choices/config.yaml')
          >>> sca2(["typing_a=c++", "typing_b=c++"]) 
          {'typing_a': 'hard', 'typing_b': 'hard', 'typing_c': 'hard'}

        Looking at the source file for :ref:`load_with_choices/config.yaml`, the |load| and |choices| modifiers in node ``'typing_a'`` prevent us from setting the final value directly:

        .. doctest:: SolConfArg
          :options: +NORMALIZE_WHITESPACE

          >>> import traceback
          >>> try:
          ...   sca2(["typing_a=soft"])
          ... except Exception:
          ...   print(traceback.format_exc())
          Traceback (most recent call last):
              ...
          ValueError: The resolved value of `ParsedNode@'typing_a'<...>` is `soft`, 
            but it must be one of `('python', 'c++')`.
              ...
          soleil.solconf.exceptions.ResolutionError: Error while resolving node 
            `ParsedNode@'typing_a'<...>`.
              ...
          soleil.solconf.exceptions.ModificationError: Error while applying modifier 
            `functools.partial(<function load at 0x...>, subdir='typing', ext='.yaml')` 
            to node `ParsedNode@'typing_a'<...>`.

        This problem can be avoided using a root clobber override:

        .. doctest:: SolConfArg

           >>> sca2(["typing_a*=soft"])
           {'typing_a': 'soft', 'typing_b': 'hard', 'typing_c': 'hard'}


        .. _source clobber:

        .. rubric:: Source clobber

        In the case where a path is specified in the initializer, it can still be overriden using a root clobber assignment, *but doing so has a disadvantage*:

        .. doctest:: SolConfArg

          # Use a source clobber assignment **=<path> instead of this!
          >>> sca2(['.*={"_::load,promote": ' + examples_root + 'yaml/colors/colors_config.yaml}'])
          {'base': 'red', 'secondary': 'green', 'fancy_base': 'fuscia', 'fancy_secondary': ...

        Besides verbosity, the disadvantage of this approach is that the original ``config_source`` will still be loaded before the clobber assignment override is carried out. The **source clobber**  special syntax ``**=<path>`` has the same effect but is less verbose and avoids this drawback:

        .. doctest:: SolConfArg

          # Source clobber assignment must be the first argument in the overrides list
          >>> sca2([f'**={examples_root}/yaml/colors/colors_config.yaml'])
          {'base': 'red', 'secondary': 'green', 'fancy_base': 'fuscia', 'fancy_secondary': ...

        Note that the source clobber override must be the first item in the overrides list.


        .. rubric:: Deeper overrides

        The target of an override provided to the left of the override assignment operator can consist of any valid reference string:

        .. doctest:: SolConfArg
           :options: +NORMALIZE_WHITESPACE

           >>> sca = SolConfArg(f'{examples_root}/yaml/colors/colors_config.yaml')
           >>> sca()
           {...'layout': {'shape': 'spots',...}
           >>> sca(['layout.shape=square'])
           {...'layout': {'shape': 'square',...}


        .. rubric:: Usage with ``argparse`` parsers

        .. doctest:: SolConfArg

          >>> import argparse
          >>> from soleil.solconf.cli_tools import ReduceAction
          >>> parser = argparse.ArgumentParser()

          # Setting type=sca1 implicitly sets nargs='+' and action=ReduceAction by default.
          >>> parser.add_argument('arg1', type=sca1) 
          ReduceAction(option_strings=[], dest='arg1', nargs='+', ... type=<...SolConfArg...>, ...)

          # Path required since SolConfArg initialized with no arguments!
          >>> parser.parse_args([])
          Traceback (most recent call last):
              ...
          SystemExit: 2        

          # With no overrides
          >>> parser.parse_args([f'{examples_root}/yaml/load_with_choices/config.yaml'])
          Namespace(arg1={'typing_a': 'soft', 'typing_b': 'hard', 'typing_c': 'hard'})

          # With overrides
          >>> parser.parse_args([f'{examples_root}/yaml/load_with_choices/config.yaml', "typing_a=c++", "typing_b=c++"])
          Namespace(arg1={'typing_a': 'hard', 'typing_b': 'hard', 'typing_c': 'hard'})



        .. note::

          *Help! I'm getting the error message* ``AttributeError: 'str' object has no attribute 'pop'`` *!*

          Using :class:`SolConfArg` argument instances as the ``type`` keywork argument  in a ``ArgumentParser.add_argument`` call requires that ``action=ReduceAction``  keyword value be used as well. This keywork value is set by default when  ``type`` is a :class:`SolConfArg` instance. Have you explicitly set the ``action`` keyword argument to a different value?

        """
        self.config_source = config_source

    @property
    def DFLT_ARGPARSE_KWARGS(self):
        """
        Sets the default ``argparser.add_argument`` keyword argument values to use when this instance is used as the ``type`` keyword argument.
        """
        return {'nargs': '+' if self.config_source is None else '*',
                'action': ReduceAction}

    def __call__(self,  overrides: Optional[List[str]] = None):
        """
        If the object was initialized without specifying a ``config_source``, then the first entry of ``overrides`` must contain it.

        .. rubric:: Workflow:

        1) Load the configuration file specified by ``config_source`` to create a :class:`SolConf` object. Do not apply modifiers during :class:`SolConf` initialization..
        2) For each override:

          1) For consistency with :class:`SolConf.load` any input value is first loaded using ``yaml.safe_load`` -- this does some interpretation. For example strings that represent integers, booleans or null are converted to an integer, boolean and ``None``, respectively. The resulting value is the **raw content**.
          2) Apply all modifiers of the path implicit in the reference string (except for the last component) using :func:`~modification_heuristics.modify_ref_path`. This enables e..g, modifying ``load`` targets. Because of this application of modifiers, the order in which overrides are provided is important.
          3) Assign the override value depending on the :ref:`override type <CLI overrides>`.

        """

        overrides = overrides or []

        if overrides and (root_clobber := re.match(r'^\*\*\=(?P<path>.*$)', overrides[0])):
            # Check for source clobber
            overrides.pop(0)
            config_source = root_clobber['path']
        elif self.config_source is None:
            # If config file not previously defined, get from overrides
            config_source = overrides.pop(0)
        else:
            config_source = self.config_source

        # Load config file, do not apply modifiers yet.
        sc = SolConf.load(config_source, modify=False)

        # Alter the loaded node tree with the specified overrides.
        for ref_str, assignment_type, raw_content_str in map(self._parse_override_str, overrides):

            #
            raw_content = yaml.safe_load(raw_content_str)

            # Modify all nodes in the specified path.
            # This is required to e.g., apply load target overrides or load content that the
            # reference string refers to.
            components = Node._get_ref_components(ref_str)
            modify_ref_path(sc.root, components)

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
                    raise TypeError(f'Cannot assign raw value of node {node}.')

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
