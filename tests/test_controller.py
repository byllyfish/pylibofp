import unittest
from pylibofp.controller import Controller


class ControllerTestCase(unittest.TestCase):

    def test_init(self):
        controller = Controller()
        self.assertIsInstance(controller.apps, list)



