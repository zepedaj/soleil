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
     


Project-wide to-do's
---------------------
.. todolist::
