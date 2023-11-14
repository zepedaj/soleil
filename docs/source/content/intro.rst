Introduction
-----------------

Soleil is a Python object configuration mechanism inspired by Facebook's Hydra

# Soleil configuration files (``*.solconf`` files) use familiar Python syntax and can describe any installed Python object or function call.
# Soleil configuration files can be organized into portable, Python-like packages that can be loaded with a function call and do not need to be installed.
# Soleil includes the built-in command line tool :mod:`solex` that automatically converts any soleil package into a fully fledged, extensible command line utility that plays nicely with the builtin
   :mod:`argparse` module.
        * Soleil configuration packages can also be added directly to :mod:`argparse` parsers as arguments that resolve to the object described by the loaded configuration.
# CLI overrides also employ Python syntax
# The familiar Python syntax makes it easy to understand the capabilities and limitations of the CLI override system.
# Supports choosing whether the same object or a new instance is passed as a parameter to calls within the parameter tree.
# Debugging support ``breakpoint()`` insertion
