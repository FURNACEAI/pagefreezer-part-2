import unittest
#from mock import Mocks
from mock import MagicMock

from freezer import Freezer

class FreezerTest(unittest.TestCase):
    def test_fetch_url(self):
        mock_freezer = MagicMock()
        Freezer.fetch_url(mock_freezer, 5)
        print(mock_freezer.mock_calls())

if __name__ == '__main__':
    unittest.main()
