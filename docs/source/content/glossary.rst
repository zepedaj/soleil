Glossary
===========

.. _NST:

Native serializable type
  Python types that can be natively represented in YAML or JSON formats. These include ``int``, ``float``, ``str``, ``bool``, ``None``, ``list`` and ``dict``.

.. _reference string:

Reference string
  A string consisting of a sequence of container indices separated by one or more ``'.'`` characters. Using :math:`N>1` characters will refer to the node's :math:`(N-1)`-th ancestor. 

  **Example:** ``'var2.2..0'``.

.. _qualified name:

Qualified name
  An absolute :ref:`reference string <reference string>` that identifies a node relative to the root node and contains no consecutive ``'.'`` characters. 

  **Example:** ``'var2.0'``.

Raw content
  A python object consisting of compositions of :ref:`native_serializable types <nst>` that can containing |dstrings|, including cross-references, that is used to initialize a :class:`SolConf` object.

Node modifier
  A callable that takes a :class:`Node`-derived input and has an optional :class:`Node`-derived output.

$-string
  A string consisting of a Python expression prefixed with a ``'$:'`` that is interpreted using `Soleil's restricted Python parser <srpp def>`. 

  **Example**: ``'$: parent(r_[0])() + 2'``.

.. _srpp def:

Soleil's restricted Python parser
  A parser for evaluating a subset of the Python programming language using an extensible variable context. See 
