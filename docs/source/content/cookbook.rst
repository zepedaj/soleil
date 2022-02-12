
Cookbook
=============

.. literalinclude:: yaml/config.yaml
   :language: yaml

.. doctest::

   >>> import os
   >>> os.chdir('source/content/yaml/colors')
   >>> from soleil import SolConf

   >>> sc = SolConf.load('colors_config.yaml')
   >>> sc()
   {'base': 'red', 'secondary': 'green', 'fancy_base': 'fuscia', 'fancy_secondary': 'chartreuse', 'layout': {'shape': 'spots', 'relative_position': 'random'}, 'alternate_layout': {'shape': 'arc', 'relative_position': 'contiguous'}, 'stroke_width': 5, 'temperature': 'cold', 'target_time': numpy.datetime64('2023-10-10T10:05')}
