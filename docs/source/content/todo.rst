TODO List
=========

.. todo::

   * Add xerializable type support.

   * ``protected`` modifier that allows passing dictionaries with non-var-name keys as input.

   * AST Parser
     * Extracting/replacing python interpolation from value strings.
     * Node system - key / value nodes.
     * Key string interpolation
     * load, fromdir, other function implementations.

   * Parser
     * Documentation
     * Support passing non-string argument value to parent call
     * Support key strings with type and functions that automatically substitue in the node (or parent node) first argument.
     * 
   
   * Add a hydra-like or command-line argument processing extension.
     * Should support creation of meta variables that are not passed to the program: { @meta: {input_dimension: 100}}
     * Should have an @import command to import configs from other files or variables: {train: {db:{@from:db/, @default:mysql}       
     * Should support initializing a dictionary form another, with overwrites, e.g., {test@extends(train): {batch_size:10}} (same as @from above?)
     * Should support escaping so that parsing is not applied to some parts of the file, e.g., {@escape: {@meta:{a:1,@default:2}}}
     * Supports an @partial value. Objects with this tag will be deserialized to a callable that takes all @partial-labeled values and produces the result. E.g. {'__type__': 'sum', 'a': 1, 'b': @partial}
     * Should support substition using e.g, {{var.x}}
     * Nested variables can be specified using filesystem directories or links within the same file. E.g., train.data@from(data,@global): imagenet should assign to the train.data structure the data.imagenet structure.
     * Supports an @parargs and @prodargs command.
     * Creates and uses a virtual environment with copies of all local modules so that development can continue while training is taking places. When parallelization is used, the copy is the same for all parallel runs in a single job group.
     * Should support evaluating math expressions.
   * Add the hydra cli module from jzf_train to xerializer       
   * What happens when a @serializable() classmethod is inherited *with* modifications and *without* modifications?
   * xerializer.serializable -> Does not fail when extra arguments are passed in.
   * xerializer.abstract_type_serializer -> Rename to xerializer.abstract_types
   * Add the concept of namespaces to manages third-party plugin groups. Make it possible for these to support extending existing namespaces by just having their string name in the list of plugins.
   * Make it possible to call instance methods using the same syntax - problem with ``self`` argument being used by ``Serializer.from_serializable``.
   * Support tuple-of-string signatures that register the class as from_serializable for various signatures.
   * Add suport for signatures that are tuples of singatures -- all should be auto-registered.
   * Add support for auto-loading serializers from signature (not safe!!). Maybe not??
   * Add a way to ignore specific parameters in the @serializable decorator. Ignored parameters are not serialized. By default, ignore '_'-prefixed parameters.
   * Automatically add xerializer signature to docstring.
   * @serializable classmethods should still be serializable in their child classes.
   * Allow serialization where paths are relative to the file where the serializable is stored.
   * Allow partial deserialization, where un-registered objects do not raise an exception but rather return a special object (e.g., an object of a new `UnregisteredObjet` type). Can be used e.g., to determined which module to load.
   * Deploy to github   
   * Overhaul the extension mechanism, make it possible to inhert class and method serialization capabilities.
     


Possible syntaxes:

.. code-block:: 
   
   {@meta: {input_dimension: 100, randomization: True}}

   {train: {db:{@from:db/, @default:mysql}

db/ to define a path, db to define a variable in the file. Or db for both, and give precedence to local vars and then file system.
