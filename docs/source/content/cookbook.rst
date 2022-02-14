
Cookbook
=============

.. testsetup:: Cookbook

   import os
   os.chdir('source/content')
   from soleil import SolConf
   from rich import print


.. contents:: Examples

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


.. literalinclude:: yaml/load_with_choices/typing/c++.yaml
   :language: yaml
   :caption:

.. literalinclude:: yaml/load_with_choices/typing/python.yaml
   :language: python
   :caption:

.. doctest:: Cookbook

   >>> sc = SolConf.load('yaml/load_with_choices/config.yaml')   
   >>> print(sc())
   {'language_typing_a': 'soft', 'language_typing_b': 'soft', 'language_typing_c': 'soft'}
