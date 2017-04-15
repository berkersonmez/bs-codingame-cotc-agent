from unittest import mock, TestCase

import sys

from agent import play


referee = ['1', '2',
           '1 SHIP 13 2 3 1 5 1',
           '2 BARREL 13 6 20 0 0 0']
referee = referee * 10


class AgentUnitTests(TestCase):

    @mock.patch('builtins.input', side_effect=referee)
    def test_wood2(self, input):
        play()
        assert sys.stdout.getline().strip() == "MOVE 4 5"
        # Check the output after "13" and "Bob" are entered as well!
        assert sys.stdout.getline().strip() == "MOVE 5 5"
        assert sys.stdout.getline().strip() == "MOVE 5 6"
        assert sys.stdout.getline().strip() == "MOVE 6 6"