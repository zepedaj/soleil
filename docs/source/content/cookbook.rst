
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



Extends
---------


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
