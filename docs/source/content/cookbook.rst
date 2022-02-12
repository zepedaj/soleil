
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

.. literalinclude:: yaml/colors/colors_config.yaml
   :language: yaml
   :caption:

.. literalinclude:: yaml/colors/layouts/spots.yaml
   :language: yaml
   :caption:

.. literalinclude:: yaml/colors/layouts/rainbow.yaml
   :language: yaml
   :caption:

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
