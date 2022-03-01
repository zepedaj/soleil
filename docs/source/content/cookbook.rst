
.. _`cookbook`:

Cookbook
=============

.. testsetup:: Cookbook

   import os
   os.chdir('source/content')
   from soleil import SolConf
   from rich import print


.. contents:: Examples

Syntax
--------

Quotations
^^^^^^^^^^^

.. literalinclude:: yaml/syntax/quotations.yaml
   :language: yaml
   :caption:

.. doctest:: Cookbook
   :options: +NORMALIZE_WHITESPACE

   >>> print(SolConf.load('yaml/syntax/quotations.yaml')())
   {'example': [1, 1, 1, 1, {'a': None, 'promote': 1}]}


.. _Extends recipes:

Extends
---------

Simple
^^^^^^^

.. literalinclude:: yaml/extends/simple/config_source.yaml
   :language: yaml
   :caption:

.. literalinclude:: yaml/extends/simple/config_extends.yaml
   :language: yaml
   :caption:


.. doctest:: Cookbook
   :options: +NORMALIZE_WHITESPACE

   >>> sc = SolConf.load('yaml/extends/simple/config_extends.yaml')

   >>> sc.print_tree()
    {
        "DictContainer@''(modifiers=(<soleil.solconf.modifiers.extends object at 0x...>, <function promote at 0x...>))": [
            {"KeyNode@'*b'()": ["ParsedNode@'b'(types=(<class 'float'>,))"]},
            {"KeyNode@'*c'()": ["ParsedNode@'c'(types=(<class 'float'>,), modifiers=(<soleil.solconf.modifiers.choices object at 0x...>,))"]},
            {"KeyNode@'*d'()": ["ParsedNode@'d'()"]},
            {"KeyNode@'*a'()": ["ParsedNode@'a'()"]}
        ]
    }

   >>> print(sc())
   {'b': 3.0, 'c': 5.0, 'd': 4, 'a': 1}

With ``x_`` cross-ref
^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: yaml/extends/cross_ref/config_source.yaml
   :language: yaml
   :caption:

.. literalinclude:: yaml/extends/cross_ref/config_extends.yaml
   :language: yaml
   :caption:


.. doctest:: Cookbook
   :options: +NORMALIZE_WHITESPACE

   >>> sc = SolConf.load('yaml/extends/cross_ref/config_extends.yaml')
   >>> sc.print_tree()
    {
        "DictContainer@''(modifiers=(<soleil.solconf.modifiers.extends object at 0x...>, <function promote at 0x...>))": [
            {"KeyNode@'*a'()": ["ParsedNode@'a'(modifiers=(<function noop at 0x...>,))"]},
            {"KeyNode@'*d'()": ["ParsedNode@'d'()"]},
            {"KeyNode@'*b'()": ["ParsedNode@'b'()"]},
            {"KeyNode@'*c'()": ["ParsedNode@'c'()"]}
        ]
    }

   >>> print(sc())
    {'a': 0, 'd': 4, 'b': 2, 'c': 3}


Promotes
----------


Loading
----------

colors_config.yaml
^^^^^^^^^^^^^^^^^^^^^

.. rubric:: File structure

.. literalinclude:: yaml/colors/colors_config.yaml
   :language: yaml
   :caption:

.. literalinclude:: yaml/colors/layouts/splashes.yaml
   :language: yaml
   :caption:

.. literalinclude:: yaml/colors/layouts/rainbow.yaml
   :language: yaml
   :caption:


.. rubric:: Resolved output

.. doctest:: Cookbook

   >>> sc = SolConf.load('yaml/colors/colors_config.yaml')   
   >>> print(sc())
   {
       'base': 'red',
       'secondary': 'green',
       'fancy_base': 'fuscia',
       'fancy_secondary': 'chartreuse',
       'layout': {'shape': 'spots', 'relative_position': 'random'},
       'alternate_layout': {'shape': 'arc', 'relative_position': 'contiguous'},
       'stroke_width': 5,
       'temperature': 'cold',
       'target_time': numpy.datetime64('2023-10-10T10:05')
   }

.. _load_with_choices.yaml:

load_with_choices.yaml
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: yaml/load_with_choices/config.yaml
   :language: yaml
   :caption:

.. literalinclude:: yaml/load_with_choices/typing/python.yaml
   :language: yaml
   :caption:

.. literalinclude:: yaml/load_with_choices/typing/c++.yaml
   :language: yaml
   :caption:

.. literalinclude:: yaml/load_with_choices/typing/java.yaml
   :language: yaml
   :caption:

.. doctest:: Cookbook

   >>> sc = SolConf.load('yaml/load_with_choices/config.yaml')   
   >>> print(sc())
   {'typing_a': 'soft', 'typing_b': 'hard', 'typing_c': 'hard'}
