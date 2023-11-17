import pytest
from soleil.loader.loader import load_config
from soleil.resolvers.base import resolve
from tests.soleil.test_helpers import solconf_file


class TestSubmodule:
    def test_promoted_fails(self):
        with solconf_file(
            """
a:promoted = submodule('abc', 'def')
"""
        ) as fl:
            with pytest.raises(
                SyntaxError,
                match="Cannot apply `promoted` modifier to `submodule` overridables "
                "- either use `resolves` instead of `promoted` or `load` instead of "
                "`submodule`.",
            ):
                resolve(load_config(fl))
