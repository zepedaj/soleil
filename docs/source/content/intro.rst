.. currentmodule:: soleil.solconf

|soleil| is *(1)* a **configuration manager** that is templated, hierarchical, and cross-referential; *(2)* a **CLI builder** ; and *(3)* **experiment launcher**. It is inspired by Facebook's `Hydra <https://hydra.cc/docs/intro/>`_.

The main aim of |soleil| is to increase flexibility while reducing the amount of glue code, effort, technical debt buildup and related researcher cognitive load associated with managing machine learning model development and training experiments. 

|soleil| achieves this by enabling separation of concerns between the purely task-related code such as model definition and training scripts, and the configuration and launching code, providing facilities that minimize the required glue code between these components.

Soleil is part of a family of ML research tools that includes :mod:`xerializer` and :mod:`ploteries`.

Getting started
===============

Installation
------------------

.. code-block:: bash

  pip install soleil


Cookbook
----------

The best way to get started is to look at the examples in the :ref:`Cookbook`.

Motivation
--------------

* [TODO] Leverages the :mod:`xerializer` package to support custom type type-checking and config file or CLI object representation.

* Near-no-code CLI experiment launching.

* Leverages Python's built-in `Abstract Syntax Tree <https://docs.python.org/3/library/ast.html>`_ support.

  * Simple, rich, Python-based syntax for configuration value resolution.
  * Restricted for safety, user-extensible.

* Flexible configuration node tree system

  * Supports hidden nodes that are visible to other nodes when rendering, but not included in the final rendered configuration.
  * Can represent any argument structure - the root does not need to be a dictionary.

* [TODO] Plays nicely with `argparse <https://docs.python.org/3/library/argparse.html>`_ -- can be used to define an argparse parameter, or to auto-build a CLI from a config file.

* Simple, well-documented code base.
* Common type-checking interface
* Consistent, flexible conventions, easy to remember.
* Non-intrusive 

  * Does not auto-configure logging or output file location. 
  * Does not require a rigid configuration file structure or output file name location.

* Meaningful error messages clearly indicating configuration nodes with problems.

  * Configuration values cyclical dependencies detected automatically and signaled to the user.
  * [TODO] Config source file causing the error included in error message.



Soleil configuration objects 
===============================

Data representation
-----------------------

Soleil configuration objects (:class:`solconf.SolConf` objects) are built from compositions of *native serializable types* (i.e., those types that can be represented natively in **YAML** or **JSON** format):

   * ``int``, ``float``, ``str``, ``bool``, 
   * ``None``, 
   * ``list`` and
   * ``dict`` (with string keys that are valid variable names).

This makes it possible to represent these objects in human-readable **YAML** or **JSON** files stored in directory hierarchies.

.. rubric:: Node tree

Internally, :class:`solconf.SolConf` represents compositions of the above types using a node tree. See :ref:`Node system` for an in-depth description of the :class:`~solconf.SolConf` node tree. For most purposes, however, it suffices to know that each (nested) component of the raw content used to initialize a :class:`~solconf.SolConf` object is represented internally as a node object arranged into a tree.

.. rubric:: Basic examples

A :class:`SolConf` object is built by passing **raw content** directly to the initializer:

.. testcode:: SolConf

   from soleil import SolConf
   import traceback

   sc = SolConf('abc')

**Calling** a :class:`SolConf` object returns its **resolved** value. For simple raw content (raw content without modifiers or |dstrings|), the resolved value is the same as the original input:

.. testcode:: SolConf

   # Native types
   for raw in [1, 2.0, 'abc', [1,2,'abc']]:
     sc = SolConf(raw)
     assert sc() == raw
     
   # Dictionaries - keys must be valid variable names.
   for raw in [{'var0':0, 'var1':1, 'var2':2}]:
      sc = SolConf(raw)
      assert sc() == raw


Compositions of the native types are also valid input:

.. testcode:: SolConf

  # Base type compositions are valid too.
  raw_content = {
    'var0': [0, 1, 2, 'abc', {'var1':[3,4,'xyz']}],
    'var2': 5
  }
  assert SolConf(raw_content)() == raw_content    
     
.. _dstrings:

$-strings
-----------

The power of :class:`SolConf` objects comes in part from their ability to interpret |dstrings| -- special strings indicated by a ``'$:'`` prefix that are evaluated using the :ref:`SRPP`:

.. testcode:: SolConf

  assert SolConf('$: 1+2')() == 3 # White space after ``'$:'`` is stripped.
  assert SolConf('$: {1:[0,1], 2:[2,3]}')() == {1:[0,1], 2:[2,3]}

The |SRPP| is a  :class:`~soleil.solconf.parser.Parser` object that supports a subset of the standard Python syntax. Evaluation occurs within a user-extensible variable context (the |dstring| context) that includes several standard Python functions and types (e.g., ``range``, ``list``, ``dict``, ``int``, ``str``) as well as special node variables used in node :ref:`cross-referencing <xref>`. 

See :ref:`SRPP` for more information on supported Python grammar components, the default variable context and ways to extend it.

Escaping strings
^^^^^^^^^^^^^^^^^

All strings in raw content that begin with ``'$: '`` are evaluated as Python expressions when the node containing the content is resolved. The alternative prefix ``'\:'`` can be instead used to escape strings:

.. testcode:: SolConf

   assert SolConf('\:  $: 1+2')() == '  $: 1+2' # White space after '\:' is not ignored
   assert SolConf('\\:  $: 1+2')() == '  $: 1+2' # Equivalent, with escaped backslash
   assert SolConf(r'\:  $: 1+2')() == '  $: 1+2' # Equivalent, with Python raw string

Evaluation context
^^^^^^^^^^^^^^^^^^^^

.. todo:: Missing

Registering new names -- decorator syntax, function syntax.

Included context.

.. _Dictionaries with arbitrary keys:

Dictionaries with arbitrary keys
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Currently, soleil only supports :class:`DictContainer` nodes with string keys that are valid variable names. However, arbitrary dictionaries can be built in three different ways.

One way is to use |dstrings|:

.. doctest:: SolConf
   
   >>> print(SolConf("$: {True: 'abc', 2: 'def', 3.0: 'ghi', None: 'jkl'}")())
   {True: 'abc', 2: 'def', 3.0: 'ghi', None: 'jkl'}

.. todo:: Missing

A second way to specify dictionaries with non-variable key names is to leverage the default :mod:`xerializer` post-processor:

.. doctest:: SolConf

   >>> print(SolConf({
   ...  '__type__': 'dict', 
   ...  'value': [(True, 'abc'), 
   ...             (2, 'def'), 
   ...             (3.0, 'ghi'), 
   ...             (None, 'jkl')]
   ... })())
   {True: 'abc', 2: 'def', 3.0: 'ghi', None: 'jkl'}

Using the post-processor further makes it possible to use any hashable registered with :mod:`xerializer` as a dictionary key:

.. doctest:: SolConf

   >>> print(SolConf({
   ...  '__type__': 'dict', 
   ...  'value': [
   ...     [{'__type__': 'tuple', 'value': [0,1]}, 0],
   ...     [{'__type__': 'np.datetime64', 'value': '2020-10-10'}, 1]
   ... ]})())
   {(0, 1): 0, numpy.datetime64('2020-10-10'): 1}

.. todo:: Add explanation of post_processor and the default xerializer post-processor.


Yet a third way to specify dictionaries with non-variable key names is to use the |cast| modifier:

.. doctest:: SolConf

   >>> print(SolConf({'_::cast(dict),promote': [[(0,1), 0], ["$: dt64(\'2020-10-10\')", 1]]})())
   {(0, 1): 0, numpy.datetime64('2020-10-10'): 1}

.. _xref:

Cross-references
-----------------

Raw content used to initialize :class:`~solconf.SolConf` objects can contain cross-references. To facilitate this, soleil automatically injects three nodes as variables into the |dstring| evaluation context:

  * **Root node variable** |ROOT_NODE_VAR_NAME| -- the *root node*;
  * **Current node variable** |CURRENT_NODE_VAR_NAME| -- the node where the |dstring| is defined;
  * **File root node variable** |FILE_ROOT_NODE_VAR_NAME| -- the current file's root node, *i.e.*, the highest-level node of the configuration file where the current node is defined;
  * **Extended node variable**  |EXTENDED_NODE_VAR_NAME| -- Available during application of the :func:`~soleil.solconf.modifiers.extends` modifier.

Note that any or all of |ROOT_NODE_VAR_NAME|, |CURRENT_NODE_VAR_NAME|, |FILE_ROOT_NODE_VAR_NAME| and |EXTENDED_NODE_VAR_NAME| could point to the same node. Any of the these variables can be used to create cross-references using :ref:`chained indices <with indices>` or :ref:`reference strings <with reference strings>`:

.. todo:: Add examples for |FILE_ROOT_NODE_VAR_NAME| and |EXTENDED_NODE_VAR_NAME|.

.. doctest:: SolConf

   >>> sc = SolConf({
   ...   'var1': {
   ...      'subvar1': 2,
   ...	    'subvar2': 3
   ...	  },
   ...
   ...   # Chained index cross-ref
   ...   'var2': "$: r_['var1']['subvar1']()",
   ...
   ...   # Ref string cross-ref
   ...   'var3': "$: n_('..var1.subvar2')"
   ... })

.. doctest:: SolConf

   >>> sc() # Resolve the object
   {'var1': {'subvar1': 2, 'subvar2': 3}, 'var2': 2, 'var3': 3}

See the :ref:`Cookbook` for more examples.


Soleil-enabled CLIs
======================

``SolConfArg`` support for ``argparse``
---------------------------------------------------------

Soleil provides the |SolConfArg| class, instances of which can be used as the value of the ``type`` keyword argument when defining |argparse| argument parsers.

See the |SolConfArg| class documentation for usage.


Executing/examining configurations with ``solex``
--------------------------------------------------

Soleil includes the ``solex`` script that, together with ``xerializable``-enabled configurations that load ``serializable`` callables, can be used to execute configuration files without the need for any extra glue code. Internally, ``solex`` employs a single |SolConfArg| argument that supports override nodes or their values directly from the CLI -- see the |SolConfArg| documentation for syntax.

The ``solex`` script takes a ``--print`` argument that can be used to examine the contents of the configuration file without executing the configuration (configuration execution is carried out by the post-processor). See the ``solex`` help message for usage:

.. todo:: Make the contents of this block be taken directly from the solex command.

.. code-block:: bash

    user@machine:~$ solex -h
    usage: solex [-h] [--modules [MODULES [MODULES ...]]] [--print {final,resolved,tree,tree-no-modifs}] conf [conf ...]

    positional arguments:
      conf                  The path of the configuration file to launch, and optionally, any argument overrides.

    optional arguments:
      -h, --help            show this help message and exit
      --modules [MODULES [MODULES ...]]
			    The modules to load before execution - can be used to register xerializable handlers.
      --print {final,resolved,tree,tree-no-modifs}
			    Prints ('final') the final value, after the post-processor is applied, ('resolved') the resolved 
			    contents before applying the post-processor or ('tree') the node tree, optionally ('tree-no-modifs') 
			    before applying modifications.

.. _Node system:



Node system
============

:class:`~solconf.SolConf` objects construct  a node-tree from raw input content. Understanding the structure of this tree is useful for advanced use. 

Workflow
----------

.. graphviz::
   :caption: |SolConf| creation, modification and resolution workflow.

   digraph foo {       
       node [shape=box,style="filled",fillcolor=azure3];

       subgraph cluster_0 {	 
        label = "SolConfArg()"
	fontname = "courier"
	style = filled
	fillcolor = chocolate1	
	subgraph cluster_1 {
	  fillcolor = cadetblue2
	  label = "SolConf.load()"
	  "YAML file" -> "Read file" -> "YAML parse" -> "SolConf1";
	 }	 
	 "SolConf1" -> "Apply CLI overrides"
	 "CLI overrides" -> "YAML parse values" -> "Apply CLI overrides" -> "SolConf.modify_tree()" ;
       }
       "SolConf.modify_tree()" -> resolve

       subgraph cluster_2 {
         style=filled
         fillcolor=gold1
         "Python object" -> SolConf2;
       }
       SolConf2 -> resolve
       

       #
       resolve -> "Post-process\n(xerializer-based by default)";

       # Input nodes       
       "YAML file" [shape=diamond, fillcolor=limegreen];
       "CLI overrides" [shape=diamond, fillcolor=limegreen];
       "Python object" [shape=diamond, fillcolor=limegreen];

       # Code blocks.       
       SolConf1 [fontname="Courier", label="SolConf()"]
       SolConf2 [fontname="Courier", label="SolConf()"]
       "SolConf.modify_tree()" [fontname="Courier"]

       # Other blocks
       resolve [label="Resolve nodes + modify values"]

   }

Node types
-----------

:class:`solconf.SolConf`  node trees can have nodes of the following types:

DictContainer
     :class:`dict_container.DictContainer` nodes represent Python dictionaries with keys that are valid variable names. Their children nodes must be of type :class:`dict_container.KeyNode`. Currently, dictionary containers only support string keys that are valid variable names. But arbitrary Python dictionaries can be built using |dstrings| -- see :ref:`Dictionaries with arbitrary keys`.
KeyNode
     :class:`~dict_container.KeyNode`  nodes contain a string key that is a valid variable name and a child node :attr:`KeyNode.value <dict_container.KeyNode.value>` that is of any of the three other node types. :class:`~dict_container.KeyNode` nodes always have a parent that is a :class:`~dict_container.DictContainer`. Key nodes play a special role discussed :ref:`here <Key nodes>`.
ListContainer
     :class:`containers.ListContainer` nodes represent Python lists and can contain nodes of any type except for type :class:`~dict_container.KeyNode`.
ParsedNode
     :class:`nodes.ParsedNode` nodes represent tree leafs -- they must always be either the root node, or a child of a :class:`~dict_container.KeyNode` or :class:`containers.ListContainer` node. When the :class:`nodes.ParsedNode`'s raw content is a string, |dstring| evaluation rules are applied to it. Otherwise, the raw value is passed on directly when resolving the node.

The types of nodes are designed to cover all :ref:`native serializable types <NST>`.


Node tree example
^^^^^^^^^^^^^^^^^^

Raw content consisting of native types is converted by the :class:`~solconf.SolConf` initializer into a tree consiting of nodes of the above type.  As an example, consider the code:

.. _example code:

.. testcode:: SolConf

   raw_content = {
    'var1': 1,
    'var2': [2,3,'$:1+3']}

   sc = SolConf(raw_content)

The object's node tree will have the following structure:

.. _example graph:

.. graphviz::
   :caption: A node tree corresponding to the code snippet :ref:`above <example code>`. Node types are indicated to the left of the '@' character, and :ref:`qualified names <qualified name>` in the single-quoted string after the '@' character. For parsed nodes, the raw content is indicated in parentheses.

   digraph foo {

     node [shape=box,style=rounded]

     root [label="DictContainer@''"]
     var1_key [label="KeyNode@'*var1'"] 
     var2_key [label="KeyNode@'*var2'"]
     var1_val [label="ParsedNode@'var1' (1)"]
     var2_val [label="ListContainer@'var2'"]
     
     var2_val0 [label="ParsedNode@'var2.0' (2)"]
     var2_val1 [label="ParsedNode@'var2.1' (3)"]
     var2_val2 [label="ParsedNode@'var2.2' ('$:1+3')"]

     root -> var1_key;
     root -> var2_key;
     var1_key -> var1_val;
     var2_key -> var2_val;

     var2_val -> var2_val0;
     var2_val -> var2_val1;
     var2_val -> var2_val2;
   }

.. todo:: 

   Improvments to the above graph:

   1. Add and color-code node type, node qual_name, and value, raw content
   2. Use square, rounded-corner nodes with arrows that enter the node vertically.

.. _Key nodes:

Key nodes
----------

Key nodes offer special syntax that enables **node typing** with automatic type-checking, and special node behavior through **node modifiers** -- callables that can modify nodes or the node tree.

.. note:: The :func:`~soleil.solconf.modifiers.fuse` modifier offers an alternative syntax to specify node types and modifiers.

.. _raw key syntax:

.. rubric:: Raw key syntax

Node types and modifiers are specified in raw content using string keys with one of the following special syntaxes (raw keys):

.. code-block::

   '{key}'                     # Non-decorated key
   '{key}:{types}'             # Type-only decorated key
   '{key}::{modifiers}'        # Modifier-only decorated key
   '{key}:{types}:{modifiers}' # Type and modifier decorated key.

**Key** must contain a valid python variable name. **Types** and **modifiers**, on the other hand, must be valid python expressions returning, respectively,

  * a type or type tuple and 
  * a modifier or modifier tuple.

Both expressions will be evaluted using the :attr:`SolConf.parser <solconf.SolConf.parser>` object, hence using the same variable context as used for |dstrings|.

Note that the types and modifiers defined in a raw key will be applied to the key node's |KeyNode.value| node.


Type checking
^^^^^^^^^^^^^^

As an example, the following dictionary has an ``int``-typed entry and a ``str`` typed entry:

.. doctest:: SolConf

   >>> print(SolConf({'val1:int':1, 'val2:str':'abc'})())
   {'val1': 1, 'val2': 'abc'}

Attempting to resolve a :class:`SolConf` object that would return a value of an invalid type raises an exception:

.. doctest:: SolConf

   >>> SolConf({'val1:int' : 1.0})()
   Traceback (most recent call last):
      ...
   soleil.solconf.exceptions.ResolutionError: Error while resolving node `ParsedNode@'val1'` (full traceback above): `Invalid type <class 'float'>. Expected one of (<class 'int'>,).`

Type tuples are also valid:

.. doctest:: SolConf

   >>> print(SolConf({'val1:float,bool' : False})())
   {'val1': False}

   >>> SolConf({'val1:float,bool' : 'abc'})()
   Traceback (most recent call last):
      ...
   soleil.solconf.exceptions.ResolutionError: Error while resolving node `ParsedNode@'val1'` (full traceback above): `Invalid type <class 'str'>. Expected one of (<class 'float'>, <class 'bool'>).`

.. todo:: The above examples do not check the error message strictly enough. Only the exception type is checked.



.. todo:: Add docs for typing with xerializer string signatures.

Node modifiers
---------------

Node modifiers are callables that take a :class:`Node` as an argument and optionally output a new node. They are used to modify the node or node tree and are created using the :ref:`raw-key syntax <raw key syntax>` or the specifal |fuse| modifier.


One example application of node modifiers is to mark a node as **hidden**, meaning that it is visible to the parser and hence |dstrings|, but its resolved content is not included in the :class:`~solconf.SolConf` object's final resolved content. This behavior is useful to define meta-data used to create the configuration that is however not part of the configuration.

.. doctest:: SolConf

   >>> SolConf({'a': '$:r_("b")+1', 'b::hidden': 2})()
   {'a': 3}

Another useful application of node modifiers is to **promote** value nodes inside single-key :class:`~dict_containers.DictContainer` nodes -- i.e., to replace the container node by its single value node, in effect extending typing and modifier support to non-:class:`~dict_container.KeyNode` nodes (see also :ref:`Decorating non-key nodes`):

.. doctest:: SolConf
   :options: +NORMALIZE_WHITESPACE

   >>> SolConf({'a:int:promote':  0})()
   0
   >>> try:
   ...   SolConf({'a:int:promote':  0.0})()
   ... except:
   ...   print(traceback.format_exc())
    Traceback (most recent call last):
    ...
    TypeError: Invalid type <class 'float'>. Expected one of (<class 'int'>,).
    ...
    soleil.solconf.exceptions.ResolutionError: Error while resolving node `ParsedNode@''`.

Chaining
^^^^^^^^^

Nodes can have a tuple of modifiers as their :attr:`Node.modifiers <soleil.solconf.nodes.Node.modifiers>` attribute that will be applied sequentially. Each modifier in the sequence can optionally output a new node object, in which case subsequent modifiers will be applied to this returned node, as illustrated by the following code snippet from the :meth:`KeyNode.modify <dict_container.KeyNode.modify>` method:

.. code-block::

   node = self
   for modifier in modifiers:
     node = modifier(node) or node

.. rubric:: Effect of modifier order

Applying modifiers sequentially to the returned node, as illustrated above, increases modifier flexibility. One consequence of this mechanism to keep in mind, however, is that modifier order might affect the results:

.. doctest:: SolConf
   :options: +NORMALIZE_WHITESPACE

   # The choices modifier is applied to the fused node.
   >>> try:
   ...   SolConf({'_::fuse,choices(1,2,3)': {'value': 4}})()
   ... except Exception:
   ...   print(traceback.format_exc())
    Traceback (most recent call last):
    ...
    ValueError: The resolved value of `ParsedNode@'_'` is `4`, but it must be one of `(1, 2, 3)`.
    ...

   # The choices modifier is applied to the disarded, un-fused dictionary container node.
   # The discarded node is never evaluated, and hence `choices` is not enforced.
   >>> SolConf({'_::choices(1,2,3),fuse': {'value': 4}})()
   {'_': 4}
   

For a discussion of modifier evaluation timing protcols, see the :class:`~dict_container.KeyNode` and :class:`~solconf.SolConf` documentation.

A list of builtin modifiers automatically injected into the parser context can be found in the documentation for module :mod:`soleil.solconf.modifiers`.

``__getitem__`` automatic modification
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Node modifications is delayed as much as possible in order to enable :ref:`CLI overrides` to be applied that will affect, e.g., the way in which |load| modifiers operate. Generally, the tree is first built completely and then the entire tree is modified recursively. The recursive tree modification is required because there are various modifiers (|load|, |extends|, |fuse|, |promote|) that modify the node tree. 

The  |extends| modifier, in particular, will further depend on other nodes. In order to make these dependencies transparent to the user, |Node| implements a special :meth:`~soleil.solconf.nodes.Node.__getitem__` method that modifies each node before attempting to get one of its children. Hence, any call to :meth:`~soleil.solconf.nodes.Node.__getitem__` (or :meth:`~soleil.solconf.nodes.Node.__call__`) will modify the tree partially. This can interfere with the way in which overrides operate on nodes with |load| modifiers.

.. todo:: Examples of problem? Solution for this?

.. _Decorating non-key nodes:

Non-key node types and modifiers
---------------------------------

.. todo:: Need to discuss |fuse| as well.

Modifiers and types can only be specified from raw content for key nodes, but the ``promote`` modifier offers a workaround that enables modification and typing of non-key nodes. 

A key node with a ``promote`` modifier will have its parent dictionary container node replaced by its value node:

.. doctest:: SolConf

   >>> SolConf({'_::': 1})() # Without promotion
   {'_': 1}

   >>> SolConf({'_::promote': 1})() # With promotion
   1

.. rubric:: Types

Types defined on the key node will be applied to its value node, providing a mechanism for type checking non-key nodes:

.. doctest:: SolConf

   >>> SolConf({'_:int:promote': 1})()
   1

   >>> SolConf({'_:int:promote': 'wrong type'})()
   Traceback (most recent call last):
      ...
   soleil.solconf.exceptions.ResolutionError: Error while resolving node `ParsedNode@''` (full traceback above): `Invalid type <class 'str'>. Expected one of (<class 'int'>,).`


.. rubric:: Modifiers

Modifiers will likewise be applied to the promoted value node, enabling, for example, non-key node choice verification:

.. doctest:: SolConf
   :options: +NORMALIZE_WHITESPACE

   >>> SolConf({'_:int:promote,choices(1,2,3)': 3})()
   3

   >>> try:
   ...   SolConf({'_:int:promote,choices(1,2,3)': 4})()
   ... except Exception:
   ...   print(traceback.format_exc())
   Traceback (most recent call last):
   ...
   ValueError: The resolved value of `ParsedNode@''` is `4`, but it must be one of `(1, 2, 3)`.
   ...
   soleil.solconf.exceptions.ResolutionError: Error while resolving node `ParsedNode@''`.


Referencing nodes
-------------------

.. _with indices :

... with indices
^^^^^^^^^^^^^^^^^

Container nodes expose a :meth:`~Node.__getitem__` method that enables natural, chainable, dictionary- or list-like access:

.. testcode:: SolConf

   r_ = sc.root # This assignment is done automatically in $-string contexts.
   r_['var2'][2]

:class:`SolConf` further exposes a :meth:`~SolConf.__getitem__` that is an alias to the root node's :meth:`~Node.__getitem__` method:

.. testcode:: SolConf

   assert (
     r_['var2'][2] is 
     sc['var2'][2]
   )


Note that accessing children nodes in this manner will return another node. As usual, the returned node can be resolved with its :class:`~Node.__call__` method:

.. testcode:: SolConf

   assert r_['var2'][2]() == 4

.. rubric:: Key vs. value node indexing syntax

Accessing a dictionary container's node using the key string produces not the :class:`~dict_container.KeyNode` that is a direct child of the container, but rather the node contained in the :class:`KeyNode.value` attribute. 

The key node can be accessed instead by pre-pending the key string with ``'*'``:

.. testcode:: SolConf

   from soleil.solconf.dict_container import KeyNode

   assert type(r_['var2']) is not KeyNode
   assert type(r_['*var2']) is KeyNode

   assert r_['var2'].parent is r_['*var2']
   assert r_['*var2'].parent is r_

This indexing syntax is meant to make node indexing behave like standard dictionary indexing.

.. _with reference strings :

... with reference strings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. todo:: 

   Reference strings currently impose the constrain that all soleil dictionary keys contain valid variable names. This excludes generic python dictionaries, and does not even include all possible YAML or JSON-representable dictionaries. To remove this constraint:
   
     * Extend reference string suppor to include all YAML dictionary keys (ints, floats, None, bool, string).
     * Use reference string syntax ``node(ref string)`` to support only some types of indexing, and require the more verbose index-based syntax ``node[idx0]..[idxN]()`` for full flexibility -- this would require dropping/changing :attr:`nodes.Node.qual_name`.


Reference strings offer another way to refer to nodes in the node tree. Reference strings consist of a sequence of container indices separated by one or more ``'.'`` characters. They can be used as arguments to a node's :meth:`soleil.solconf.nodes.Node.__getitem__` method to get another node from the tree, or to the :meth:`soleil.solconf.nodes.Node.__call__` to get the resolved value of that node.

.. doctest:: SolConf

   >>> r_['var2.2']
   ParsedNode(..., raw_value='$:1+3')
   >>> r_('var2.2')
   4


In both cases, the reference string is interpreted relative to the node that it is applied to:

.. doctest:: SolConf

   >>> r_['var2.0']  is r_['var2']['0'] # r_['var2'][0] also valid
   True

A sequence of :math:`N>1` ``'.'`` characters in a reference string can be used to refer to the node's :math:`(N-1)`-th ancestor:

.. testcode:: SolConf

   assert (
     r_['var2.2..0'] is 
     r_['var2.0'] )

A reference string can also be passed directly to a node's :meth:`~Node.__call__` method in order to resolve the referenced node using more compact syntax:

.. testcode:: SolConf

   # From the root   
   assert r_('var2.2..0') == 2
   assert r_('var2.0') == 2
   assert r_['var2'][0]() == 2 # Equivalent index-based syntax.

   # From node
   node = r_['var2']
   assert node('2..0') == 2
   assert node('0') == 2
   assert node[0]() == 2 # Equivalent index-based syntax.

Note that, similarly to index references, reference strings skip nodes of type :class:`~dict_container.KeyNode`. To access a key node, prepend the node's name with a ``'*'`` character :

.. doctest:: SolConf

  >>> key_node = r_['*var2']  # Access the key node.
  >>> value_node = r_['var2'] # Access the key node's value node.

  >>> print(key_node, '|', value_node)
  KeyNode@'*var2' | ListContainer@'var2'
  >>> print(value_node.parent) # The value node's parent is the key node.
  KeyNode@'*var2'

Key node skipping also happens when accessing ancestors using dot sequences:

.. doctest:: SolConf

  >>> print(value_node.parent)
  KeyNode@'*var2'
  >>> print(value_node['..'])
  DictContainer@''    


.. todo:: Example
 
... with qualified names
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Nodes expose a :ref:`qualified name <qualified name>` in attribute :attr:`~Node.qual_name` that is a reference string relative to the root node and with no consecutive ``'.'`` characters:

.. doctest:: SolConf

   >>> node = r_['var2.2..0']
   >>> print(node)
   ParsedNode@'var2.0'
   >>> assert node.qual_name == 'var2.0'
   >>> print(r_[node.qual_name])
   ParsedNode@'var2.0'

Being root-relative reference strings in canonical form, qualified names can also be used to conveniently refer to a node's resolved value:

.. doctest:: SolConf

   >>> print(r_('var2.0'))
   2

Note that a node's string representation consists of the node's type, followed by an ``'@'`` character and the single quote-quoted qualified name for the node:

.. doctest:: SolConf

   >>> print(r_)
   DictContainer@''

   >>> print(r_['var2'][0])
   ParsedNode@'var2.0'

