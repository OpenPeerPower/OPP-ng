"""The tests the Graph component."""

import unittest

from openpeerpower.setup import setup_component

from tests.common import get_test_open_peer_power, init_recorder_component


class TestGraph(unittest.TestCase):
    """Test the Google component."""

    def setUp(self):  # pylint: disable=invalid-name
        """Set up things to be run when tests are started."""
        self.opp = get_test_open_peer_power()

    def tearDown(self):  # pylint: disable=invalid-name
        """Stop everything that was started."""
        self.opp.stop()

    def test_setup_component(self):
        """Test setup component."""
        self.init_recorder()
        config = {"history": {}, "history_graph": {"name_1": {"entities": "test.test"}}}

        assert setup_component(self.opp, "history_graph", config)
        assert dict(self.opp.states.get("history_graph.name_1").attributes) == {
            "entity_id": ["test.test"],
            "friendly_name": "name_1",
            "hours_to_show": 24,
            "refresh": 0,
        }

    def init_recorder(self):
        """Initialize the recorder."""
        init_recorder_component(self.opp)
        self.opp.start()
