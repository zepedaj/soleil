TODO List
=========

General to-do's
----------------
.. todo::

   * Add xerializable type support.
   * Add CLI support

   * AST Parser
     * Improve extracting/replacing python interpolation from value strings (colon separator only valid in brackets or within strings).

   
   * Add a hydra-like or command-line argument processing extension.
     * Should support initializing a dictionary form another, with overwrites, e.g., {test@extends(train): {batch_size:10}} (same as @from above?)
     * Supports an @partial value. Objects with this tag will be deserialized to a callable that takes all @partial-labeled values and produces the result. E.g. {'__type__': 'sum', 'a': 1, 'b': @partial}
     * Nested variables can be specified using filesystem directories or links within the same file. E.g., train.data@from(data,@global): imagenet should assign to the train.data structure the data.imagenet structure.
     * Supports an @parargs and @prodargs command.
     * Creates and uses a virtual environment with copies of all local modules so that development can continue while training is taking places. When parallelization is used, the copy is the same for all parallel runs in a single job group.

   * Deploy to github


Major overhaul
----------------
 * Use an inheritance system based on Python classes. To support arbitrary names, use attribute name mangling, or an attribute prefix like '__key__'. E.g., attribute 'batch_size', would become '__key__batch_size'. Assigning to a derived class should change the value of that class and not the parent class. Appending to dictionaries, however, would come with the same nuances as in Python classes.
 * Modifying a node automatically modifies the path from the root to the node, starting at the root. Nodes can become unbound, and this should be checked for.
 * While being modified, a node's `modified` attribute should be set to, e.g., 'IN_PROGRESS'. Attempting to modify a node with modif state 'IN_PROGRESS' should raise a cycle dependency error.
 * Load should load a single copy always. This copy should be stored in a separate tree, and all other loads of the same file should instead use that copy. The load target should end up deriving from the loaded copy.
 * Tree visualizations should display loads and derives in a way that preserves relationships to make it compact.


Project-wide to-do's
---------------------
.. todolist::
