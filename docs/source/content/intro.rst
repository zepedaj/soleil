
.. currentmodule:: soleil.solconf

|soleil| is *(1)* a **configuration manager** that is templated, hierarchical, and cross-referential; *(2)* a **CLI builder** ; and *(3)* **experiment launcher** inspired by Facebook's `Hydra <https://hydra.cc/docs/intro/>`_.

The main aim of |soleil| is to increase flexibility while reducing the amount of glue code, effort, technical debt buildup and related researcher cognitive load associated with managing machine learning model development and training experiments. |soleil| achieves this by enabling separation of concerns between the purely task-related code such as model definition and training scripts, and the configuration and launching code, while minizing the glue code between these two main components to ease modification and experimentation.

Soleil is part of a family of packages that share this aim and includes :mod:`xerializer` and :mod:`ploteries`.

Motivation
==========

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


Installation
============

.. code-block:: bash

  pip install soleil

Getting started
===============


Soleil configuration objects 
===============================

Basic configuration objects
----------------------------------

Soleil configuration objects (:class:`solconf.SolConf` objects) are built from compositions of *native serializable types* (i.e., those types that can be represented natively in **YAML** or **JSON** format):

   * ``int``, ``float``, ``str``, ``bool``, 
   * ``None``, 
   * ``list`` and
   * ``dict`` (with string keys that are valid variable names).

This makes it possible to represent these objects in human-readable **YAML** or **JSON** files stored in directory hierarchies.

.. rubric:: Basic examples

A :class:`SolConf` object is built by passing raw content directly to the initializer:

.. testcode:: SolConf

   from soleil import SolConf

   sc = SolConf('abc')

Calling a :class:`SolConf` object returns its **resolved** value. For simple raw content (raw content without modifiers or |dstrings|), the resolved value is the same as the original input:

.. testcode:: SolConf

   # Base types
   for raw in [1, 2.0, 'abc', [1,2,'abc']]:
     sc = SolConf(raw)
     assert sc() == raw
     
   # Dictionaries - keys must be valid variable names.
   for raw in [{'var0':0, 'var1':1, 'var2':2}]:
      sc = SolConf(raw)
      assert sc() == raw


Compositions of these base types are also valid input:

.. testcode:: SolConf

  # Base type compositions are valid too.
  raw_content = {
    'var0': [0, 1, 2, 'abc', {'var1':[3,4,'xyz']}],
    'var2': 5
  }
  assert SolConf(raw_content)() == raw_content    
     
|dstrings|
-----------

The power of :class:`SolConf` objects comes from their ability to interpret |dstrings| -- special strings indicated by a ``'$:'`` prefix that are evaluated using |soleil|'s :ref:`Restricted Python Parser`:

.. testcode:: SolConf

  assert SolConf('$: 1+2')() == 3 # White space after ``'$:'`` is stripped.
  assert SolConf('$: {1:[0,1], 2:[2,3]}')() == {1:[0,1], 2:[2,3]}

|dstrings| are evaluated using a :class:`~soleil.solconf.parser.Parser` object that supports a subset of the standard Python syntax. Evaluation occurs within a user-extensible variable context (the |dstring| context) that includes several standard Python functions and types (e.g., ``range``, ``list``, ``dict``, ``int``, ``str``) as well as special node variables used in node :ref:`cross-referencing <xr>`.

See :ref:`Restricted Python Parser` for more information on supported Python grammar components, the default variable context and ways to extend it.

Escaping strings
^^^^^^^^^^^^^^^^^

All strings in raw content that begin with ``'$: '`` are evaluated as Python expressions when the node containing the content is resolved. This behavior can be overriden by instead prefixing the string with ``'\:'``:

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

Currently, soleil only supports :class:`DictContainer` nodes with string keys that are valid variable names. However, arbitrary dictionaries can be built using |dstrings|:

.. doctest:: SolConf
   
   >>> print(SolConf("$: {True: 'abc', 2: 'def', 3.0: 'ghi', None: 'jkl'}")())
   {True: 'abc', 2: 'def', 3.0: 'ghi', None: 'jkl'}

.. todo:: Missing

.. _xr:

Cross-references
-----------------

Raw content used to initialize :class:`SolConf` objects can contain cross-references. To facilitate this, soleil automatically injects three nodes as variables into the |dstring| evaluation context:

  * Variable |ROOT_NODE_VAR_NAME| refers to the *root node*.
  * Variable |CURRENT_NODE_VAR_NAME| refers to the *current node* -- the node where the |dstring| is defined.
  * Variable |FILE_ROOT_NODE_VAR_NAME| refers to the current file's root node -- the highest-level node of the configuration file where the current node is defined. This is possibly the same as ``n_``. It will not be defined if the current node was not defined in a file.

Any of these variables described above can be used to create cross-references using :ref:`chained indices <with indices>` or :ref:`reference strings <with reference strings>`:

.. testcode:: SolConf

   sc_xr = SolConf({
	      'var1': {
	        'subvar1': 2,
		'subvar2': 3
		},
	      # Chained index cross-ref
	      'var2': "$: r_['var1']['subvar1']()",
	      # Ref string cross-ref
	      'var3': "$: n_('..var1.subvar2')"
	      })

   assert sc_xr() ==  {
	      'var1': {
	        'subvar1': 2,
		'subvar2': 3
		},
	      'var2': 2,
	      'var3': 3
	      }

Node system
============

:class:`solconf.SolConf` objects construct  a node-tree from raw input content. Understanding the structure of this tree is useful for advanced use. 

Node types
-----------

:class:`solconf.SolConf`  node trees can have nodes of the following types:

DictContainer
     :class:`dict_container.DictContainer` nodes represent Python dictionaries with keys that are valid variable names. Their children nodes must be of type :class:`dict_container.KeyNode`. Currently, dictionary containers only support string keys that are valid variable names. But arbitrary Python dictionaries can be built using |dstrings| -- see :ref:`Dictionaries with arbitrary keys`.
KeyNode
     :class:`~dict_container.KeyNode`  nodes contain a string key that is a valid variable name and a child node :attr:`dict_container.KeyNode.value` that is of any of the three other node types. :class:`~dict_container.KeyNode` nodes always have a parent that is a :class:`~dict_container.DictContainer`. Key nodes play a special role discussed :ref:`here <Key nodes>`.
ListContainer
     :class:`ListContainer` nodes represent Python lists and can contain nodes of any type except for type :class:`~dict_container.KeyNode`.
ParsedNode
     :class:`ParsedNode` nodes represent tree leafs -- they must always be either the root node, or a child of a :class:`~dict_container.KeyNode` or :class:`ListContainer` node. When the :class:`ParsedNode`'s raw content is a string, |dstring| evaluation rules are applied to it. Otherwise, the raw value is passed on directly when resolving the node.

The types of nodes are designed to cover all :ref:`native serializable types <NST>`.


.. rubric:: Example

As an example, consider the following :class:`SolConf` object:

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

Key nodes offer special functionality that enables **node typing** with automatic type-checking, and special node behavior through **node modifiers**. A  **node modifier** is a callable that takes a :class:`Node`-derived input and has an optional :class:`Node`-derived output.

One example application of node modifiers is to mark a node as **hidden**, meaning that it is visible to the parser and hence |dstrings|, but its resolved content is not included in the :class:`SolConf` object's final resolved content. This behavior is useful to define meta-data used to create the configuration that is however not part of the configuration.

Another useful application of node modifiers is to **promote** value nodes inside single-key :class:`DictContainer` nodes -- i.e., to replace the container node by its single value node, in effect extending typing and modifier support to non-:class:`~dict_container.KeyNode` nodes. See :ref:`Decorating non-key nodes`.


.. rubric:: Syntax

Node types and modifiers -- collectively node decorators -- are specified in raw content using string keys with one of the following special syntaxes:

.. code-block::

   '{key}'                     # Non-decorated key
   '{key}:{types}'             # Type-only decorated key
   '{key}::{modifiers}'        # Modifier-only decorated key
   '{key}:{types}:{modifiers}' # Type and modifier decorated key.

**Key** must contain a valid python variable name. **Types** and **modifiers**, on the other hand, must be valid python expressions returning 

  * a type or type tuple and 
  * a modifier or modifier tuple, 

respectively. Both expressions will be evaluted using the :attr:`~soleil.solconf.SolConf.parser` object, hence using the same variable context as used for |dstrings|.


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
   TypeError: Invalid type <class 'float'>. Expected one of (<class 'int'>,).

Type tuples are also valid:

.. doctest:: SolConf

   >>> print(SolConf({'val1:int,float,bool' : False})())
   {'val1': False}

   >>> SolConf({'val1:int,float,bool' : 'abc'})()
   Traceback (most recent call last):
      ...
   TypeError: Invalid type <class 'str'>. Expected one of (<class 'int'>, <class 'float'>, <class 'bool'>).

.. todo:: The above examples do not check the error message strictly enough. Only the exception type is checked.



.. todo:: Add docs for typing with xerializer string signatures.

Modifiers
^^^^^^^^^^
.. todo:: Missing

.. _Decorating non-key nodes:

Docorating non-key nodes
-------------------------

.. todo:: missing


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

Reference strings offer another way to refer to nodes in the node tree. Reference strings consist of a sequence of container indices separated by one or more ``'.'`` characters. 

Using :math:`N>1` ``'.''`` characters will refer to the node's :math:`(N-1)`-th ancestor.

.. testcode:: SolConf

   assert (
     r_.node_from_ref('var2.2..0') is 
     r_.node_from_ref('var2.0') )

A reference string can also be passed directly to a node's :meth:`~Node.__call__` method in order to resolve the referenced node using more compact syntax:

.. testcode:: SolConf

   # From the root   
   assert r_('var2.2..0') == 2
   assert r_('var2.0') == 2
   assert r_['var2'][0]() == 2 # Equivalent index-based syntax.

   # From node
   node = r_.node_from_ref('var2')
   assert node('2..0') == 2
   assert node('0') == 2
   assert node[0]() == 2 # Equivalent index-based syntax.

Note that, similarly to index references, reference strings skip nodes of type :class:`~dict_container.KeyNode`. To access a key node, prepend the node's name with a ``'*'`` character :

.. doctest:: SolConf

  >>> key_node = r_.node_from_ref('*var2')  # Access the key node.
  >>> value_node = r_.node_from_ref('var2') # Access the key node's value node.

  >>> print(key_node, '|', value_node)
  KeyNode@'*var2' | ListContainer@'var2'
  >>> print(value_node.parent) # The value node's parent is the key node.
  KeyNode@'*var2'

Key node skipping also happens when accessing ancestors using dot sequences:

.. doctest:: SolConf

  >>> print(value_node.parent)
  KeyNode@'*var2'
  >>> print(value_node.node_from_ref('..'))
  DictContainer@''    


.. todo:: Example
 
... with qualified names
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Nodes expose a :ref:`qualified name <qualified name>` in attribute :attr:`~Node.qual_name` that is a reference string relative to the root node and with no consecutive ``'.'`` characters:

.. doctest:: SolConf

   >>> node = r_.node_from_ref('var2.2..0')
   >>> print(node)
   ParsedNode@'var2.0'
   >>> assert node.qual_name == 'var2.0'
   >>> print(r_.node_from_ref(node.qual_name))
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


Discussion on supporting non-variable name key :class:`~dict_container.DictContainer` objects
===============================================================================================

Pros and cons of extending dictionary support to non-variable name keys

.. rubric:: Cons

* Qualified names and ref strings would not be valid anymore.
* Would loss simple syntax for from-CLI value modifications.
* Might complicate or invalidate the '{key}:{types}:{modifiers}' syntax - how would type and modifier decorations be applied to non-string nodes?

.. rubric:: Pros
	    
* Would be able to convert any python dictionary can be converted to a :class:`~solconf.SolConf` object.
* Can fix lack of support for some YAML dictionaries. E.g., the following YAML string would fail. '{-1: 1, -2 : 2, null : 3, 3.0 : 4, True : 5, False : 6}'
* Can fix lack of support for some JSON dictionaries. E.g., '{"0" : 1, "1" : 2}'
* Possible support for |dstring| keys -- but what's the use?

.. rubric:: Possible implementations

* Only support YAML-support dictionary keys (ints, floats, None, bool, string).
* Support promoted KeyNodes that are replaced by their value node with the ``promote`` modifier:

  ..  doctest:: SolConf

      >>> SolConf({':int:promote' : 0})() # The key is the empty string here; the promoted node will be type-checked as `int` upon resolution.
      0
      >>> SolConf({0: {':bool:promote' : False}})() # The `load` modifier is applied to the parent KeyNode of key 0.
	 
	 
