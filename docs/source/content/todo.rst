Wish List
-------------

The following are various pending tasks looking for contributors:

.. todolist::

.. todo::

   * Make it possible to save a configuration so that trained models can be re-trained starting only from the output directory. Saved configurations should retain links between data.

   * Support visualization of all the options available, either at the command line or as an html-formatted value. Ideally, the representation should make obvious the links between data (e.g.,
     when a class is a derived or an assignment is to a loaded module or module variable).
   * Make the "brief" version of the id string take into account any possible name clashes when reducing parameter names. E.g. overrides to `param_1.class_A.x = 1` and `param_2.class_B.y = 2` should reduce to `'x=1'` and `'y=2'`. But overrides to `param_1.class_A.x = 1` and `param_2.class_B.x = 2` should reduce e.g., to `'param_1.x=1'` and `'param_2.x=2'`. Likewise, make it possible to specify
     overrides using short parameter names.
   * Multiply specified overrides (e.g., ``solex train.solconf a=1 b=2 a=3``) need to raise an error
   * Add a 'with hidden:' preprocessor-level directive. At first, add this to the root level only. Variables declared in this block are added to the '__soleil_default_hidden__' list.
   * Add a 'with noid:' preprocessor-level directive.
   * Documentation, github upload
   * ``type:as_type=?`` should support taking resolvables - A possible solution is to have `cast` be applied at resolution time, and the input to cast is also resolved at that time.

