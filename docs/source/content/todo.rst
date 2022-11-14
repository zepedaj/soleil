TODO List
=========

General to-do's
----------------
.. todo::

   * AST Parser
     * Improve extracting/replacing python interpolation from value strings (colon separator only valid in brackets or within strings).

   
   * Add a hydra-like or command-line argument processing extension.
     * Should support initializing a dictionary form another, with overwrites, e.g., {test@extends(train): {batch_size:10}} (same as @from above?)
     * Supports an @partial value. Objects with this tag will be deserialized to a callable that takes all @partial-labeled values and produces the result. E.g. {'__type__': 'sum', 'a': 1, 'b': @partial}
     * Nested variables can be specified using filesystem directories or links within the same file. E.g., train.data@from(data,@global): imagenet should assign to the train.data structure the data.imagenet structure.
     * Supports an @parargs and @prodargs command.
     * Creates and uses a virtual environment with copies of all local modules so that development can continue while training is taking places. When parallelization is used, the copy is the same for all parallel runs in a single job group.


   * Raise an error whenever a ??? value is not provided.

   * For ``load`` modifier: If the directory is not specified, use the name of the containing node by default. E.g., ``data::load(): default`` should be equivalent to ``data::load('data'): default``. If possible, ``data::load: default`` should also be equivalent. Increases the code dryness.

   * Deploy to github

   * Add a ``+=`` assignment operator that enables adding a new node from the command line.

   * Move `CLI overrides` and related documentation from `soleil.solconf.cli_tools.solconfarg` to `Soleil-enabled CLIs` document section.

   * Add a way to CLI-override a parameter with a (raw or resolved) value from another parameter. E.g., makes it possible to use the training set as a validation set. The current solution requires using the `derives` modifier and only works from configuration files, as modifiers cannot be specified from the command line.

   * Let `derives` modifier take a string 'str' (right no it only takes a node) as an argument, and let that correspond to node `f_['str']`.

   * When using CLI overrides, not clear at which point in the processing chain the override is applied. Before modification? Before Resolution? Before proprocessing? As the final value?

Minor
---------
 * CLI overrides of inherited properties should affect the derived node, not the node being derived.


Major overhaul
----------------
 * Use an inheritance system based on Python classes. To support arbitrary names, use attribute name mangling, or an attribute prefix like '__key__'. E.g., attribute 'batch_size', would become '__key__batch_size'. Assigning to a derived class should change the value of that class and not the parent class. Appending to dictionaries, however, would come with the same nuances as in Python classes.
 * Modifying a node automatically modifies the path from the root to the node, starting at the root. Nodes can become unbound, and this should be checked for.
 * While being modified, a node's `modified` attribute should be set to, e.g., 'IN_PROGRESS'. Attempting to modify a node with modif state 'IN_PROGRESS' should raise a cycle dependency error.
 * Load should load a single copy always. This copy should be stored in a separate tree, and all other loads of the same file should instead use that copy. The load target should end up deriving from the loaded copy.
 * Tree visualizations should display loads and derives in a way that preserves relationships to make it compact.
 * Add an "alias" modifier that makes a node a reference to another node --  this should replace the approach that does {'node': '$:source()'} to alias nodes, as that approach loses references. The node's parent and the alias's parent should be different. But what about modifiers that alter the tree... ? Modifier "derives" works similarly to this, but when the purpose is to import from another file, this creates two e.g., "train_data" variables, one in the loaded node, and one in the derived node.


Project-wide to-do's
---------------------
.. todolist::
