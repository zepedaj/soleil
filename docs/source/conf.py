# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = "soleil"
copyright = "2023, Joaquin Zepeda"
author = "Joaquin Zepeda"

# The full version, including alpha/beta/rc tags
release = "0.0.0 alpha"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx_rtd_theme",
    "sphinx.ext.todo",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"
html_logo = "images/soleil_transparent.png"
html_theme_options = {
    #    "logo_only": True,
    "display_version": True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# -- Extension configuration -------------------------------------------------
#
autoclass_content = "both"
autodoc_default_options = {
    "member-order": "bysource",
    "members": True,
    "special-members": "__call__,__getitem__,__len__",
    "ignore-module-all": True,
    "show-inheritance": True,
}
autosummary_generate = True
todo_include_todos = True


##
rst_prolog = """
.. |argparse| replace:: `argparse <https://docs.python.org/3/library/argparse.html>`__
.. |ArgumentParser| replace:: `ArgumentParser <https://docs.python.org/3/library/argparse.html#argumentparser-objects>`__
.. |climax| replace:: `climax <https://climax.readthedocs.io/en/latest/>`__
.. |SolConfArg| replace:: :class:`~soleil.cli_tools.solconfarg.SolConfArg`
.. |ast| replace:: `AST <https://docs.python.org/3/library/ast.html>`__
.. |solex| replace:: :ref:`solex <solex>`
.. |@solex| replace:: :func:`@solex <soleil.cli_tools.solex_decorator.solex>`
.. |@solex doc| replace:: :ref:`@solex decorator <@solex>`
.. |load_config| replace:: :func:`~soleil.loader.loader.load_config`
.. |load| replace:: :meth:`~soleil.resolvers.module_resolver.SolConfModule.load`
.. |visible| replace:: :meth:`~soleil.resolvers.module_resolver.modifiers.visible`
.. |var name paths| replace:: variable name paths
.. |soleil| replace:: Soleil
.. |as_type| replace:: ``as_type``
.. |as_run| replace:: ``as_type``
.. |DALLE| replace:: `DALL-E <https://openai.com/research/dall-e>`__
"""


######### Utilities
import sys, os

sys.path.insert(0, os.path.abspath("."))

from soleil.cli_tools import SolConfArg


def sort_dicts(d):
    if isinstance(d, dict):
        return dict((k, sort_dicts(v)) for k, v in sorted(d.items()))
    else:
        return d


def fix_dict_order():
    # Patch SolConfArg.__call__

    global _orig_sca_call
    _orig_sca_call = SolConfArg.__call__

    def __call__(self, *args, **kwargs):
        out = sort_dicts(_orig_sca_call(self, *args, **kwargs))
        return out

    SolConfArg.__call__ = __call__

    # Patch parser
    from argparse import ArgumentParser

    global _orig_parse_args
    _orig_parse_args = ArgumentParser.parse_args

    def parse_args(self, *args, **kwargs):
        out = _orig_parse_args(self, *args, **kwargs)
        for key in vars(out):
            setattr(out, key, sort_dicts(getattr(out, key)))

        return out

    ArgumentParser.parse_args = parse_args
