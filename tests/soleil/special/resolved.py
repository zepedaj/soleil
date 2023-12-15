from soleil.loader.loader import load_solconf
from tests.helpers import solconf_file


class TestResolved:
    def test_all(self):
        with solconf_file(
            """
class fl:
    type:as_type = open
    args:as_args = ('/tmp/tmpfile','w+')

mode:promoted = resolved(fl).mode

"""
        ) as fl:
            assert (x := load_solconf(fl)) == "w+"
