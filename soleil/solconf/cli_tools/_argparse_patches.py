import argparse
from functools import partialmethod


class ReduceAction(argparse._StoreAction):
    # Takes multiple argument strings and, instead of returning a list,
    # applies the type function to the list and returns the output.
    #
    # Implementing this requires monkey-patching argparse.ArgumentParser._get_values,
    # which is done below
    pass


# TODO: Breaks if reloading the module!
ORIG_GET_VALUES = argparse.ArgumentParser._get_values
ORIG_ADD_ARGUMENT = argparse.ArgumentParser.add_argument


def _get_values(self, action, arg_strings):
    # Monkey-patched version of ArgumentParser._get_values that implements
    # ReduceAction's mandate.
    if isinstance(action, ReduceAction):
        type_fxn = self._registry_get('type', action.type, action.type)
        return type_fxn(arg_strings)
    else:
        return ORIG_GET_VALUES(self, action, arg_strings)


def add_argument(self, *args, **kwargs):
    # Monkey-patched version of ArgumentParser._get_values that
    # supports types with default add_argument keyword args.
    if (type_kw := kwargs.get('type')) and hasattr(type_kw, 'DFLT_ARGPARSE_KWARGS'):
        kwargs = {**type_kw.DFLT_ARGPARSE_KWARGS, **kwargs}
    return ORIG_ADD_ARGUMENT(self, *args, **kwargs)


# Monkey-patch ArgumentParser
argparse.ArgumentParser._get_values = _get_values
argparse.ArgumentParser.add_argument = add_argument
