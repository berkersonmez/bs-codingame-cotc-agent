from unittest import mock, TestCase

import sys

from agent import agent


class AgentUnitTests(TestCase):

    @mock.patch('builtins.input', side_effect=['1', '4', 'Bob'])
    def test_wood2(self, input):
        agent()
        output = sys.stdout.getline().strip()
        assert output == "You are too young"
        # Check the output after "13" and "Bob" are entered as well!
        assert sys.stdout.getline().strip() == "Welcome!"