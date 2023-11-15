Wish List
-------------

.. todo::

   * X Find a way to make it possible to derive from modules. Possibilities:
        #) A function that can be used to make a module behave as a class,
        #) a pre-processor directive that automatically forces all module directives to be inside a class
        #) A special modifier (e.g., 'promote_conf', possibly default for var or class names '_') that automatically makes that variable or class the default loaded variable or class.
        #) X Modify promote so that it also promotes the meta param
   * Make it possible to save a configuration so that trained models can be re-trained starting only from the output directory. Saved configurations should retain links between data.
   * X Make it possible to override parent properties in derived classes:
        #) Have CLI overrides act after the meta param structures are created
   * Make builtins (dict, set, tuple, list) be singly resolved by having the pre-processor output a soleil-specific thin sub-class that supports adding extra attributes.

   * Add a `source` pre-proc directive that copy-pastes the code form another module with with new overrides / reqs. Loads from the sourced module should be relative to the original module's positions.
     * X Similar solution `spawn` employed
   * Support visualization of all the options available, either at the command line or as an html-formatted value. Ideally, the representation should make obvious the links between data (e.g.,
     when a class is a derived or an assignment is to a loaded module or module variable).
   * Make the "brief" version of the id string take into account any possible name clashes when reducing parameter names. E.g. overrides to `param_1.class_A.x = 1` and `param_2.class_B.y = 2` should reduce to `'x=1'` and `'y=2'`. But overrides to `param_1.class_A.x = 1` and `param_2.class_B.x = 2` should reduce e.g., to `'param_1.x=1'` and `'param_2.x=2'`. Likewise, make it possible to specify
     overrides using short parameter names.
   * Multiply specified overrides (e.g., ``solex train.solconf a=1 b=2 a=3``) need to raise an error
   * Add a 'with hidden:' preprocessor-level directive. At first, add this to the root level only. Variables declared in this block are added to the '__soleil_default_hidden__' list.
   * Add a 'with noid:' preprocessor-level directive.
   * Documentation, github upload
   * X Make it possible to load new packages in a way that can be overriden from the CLI. Currently, load_config can be used to load external pacakges, but the package cannot be overriden from the CLI.
   * ``type:as_type=?`` should support taking resolvables - A possible solution is to have `cast` be applied at resolution time, and the input to cast is also resolved at that time.

