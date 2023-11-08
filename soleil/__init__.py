from soleil.loader.loader import load_config
from soleil.resolvers.base import resolve
from soleil.cli_tools.solex import solex

__all__ = [x for x in dir() if not x.startswith("__")]


# X 1) Standalone collection resolvers
# X 2) Member is now an annotation. Can also instead use simply promote, hidden, name(value), choices(submodule) annotations as "modifiers".
# 2.1) choices is a special annotation bc it is handled by the ast so that the contents of the choices variable are the actual loaded module values
# T? 3) Implemenatation of "Missing" through type hints when resolving - get_members will include members in annotations.
# X 4) Imported variables will be ignored in the ast. The ast will also implement a special "with hidden()" block. hidden is also special (like choices) and handled by the ast.

# CLI overrides will be implented by the AST before any code executes to ensure correct propagation of variables
# Choices will initially be implemented by two parameters: a hidden "choice_name" parameter and a visible "choice_value" parameter. It will subsequently be implemented through the ast by means of type hinting.


# TODO: Documentation
