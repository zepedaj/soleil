from xerializer.cli_tools import solconf as mdl
from xerializer.cli_tools.exceptions import ResolutionCycleError

from unittest import TestCase


def path(from_node, to_node):
    branch = [to_node]
    while branch[0] is not from_node and branch[0].parent:
        branch.insert(0, branch[0].parent)
    if branch[0] is not from_node:
        raise Exception(f'There is no path from {from_node} to {to_node}.')
    return branch


def compare_cycle(cycle1, cycle2):
    return (
        len(cycle1) == len(cycle2) and
        all(n1 is n2 for n1, n2 in zip(cycle1, cycle2))
    )


class TestSolConf(TestCase):

    def test_detect_cycles(self):

        for tree, expected_cycle in [
                #
                (root := mdl.SolConf(
                    ['abc',
                     {'a': 2, 'b': '$3+1', 'c': "$'xyz'", 'd': [1, 2, "$r_('0')", "$r_[2]() + 3"]},
                     2,
                     {'e': '$2**3', 'f': '$r_()'},
                     ]).node_tree,
                 path(root, root[3]['f'])+[root]),
                #
                (r_ := mdl.SolConf(
                    ['abc',
                     {
                         'a': 2, 'b': '$r_[2]()', 'c': 3,
                         'd': [1, 2, 3, 4]},
                     '$r_[3]()',
                     {'e': '$2**3', 'f': "$r_[1]['b']()"},
                     ]).node_tree,
                 [r_[1]['b'], r_[2], r_[3], r_[3]['*f'], r_[3]['f'], r_[1]['b']]),
        ]:

            try:
                val = tree.resolve()
            except ResolutionCycleError as err:
                self.assertTrue(compare_cycle(err.cycle, expected_cycle))
            else:
                raise Exception('Expected error!')
