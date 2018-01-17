import unittest
from freezer import Freezer

class TestFreezer(unittest.TestCase):
    def test_get_limit(self):
        lim = 999999
        f = Freezer()
        f.set_limit(lim)
        self.assertEquals(f.get_limit(), lim)

    def test_get_profiling(self):
        f = Freezer()
        tests = [True, False]
        for test in tests:
            f.set_profiling(test)
            self.assertEquals(f.get_profiling(), test)

        tests = ['foo', 'bar', 123, [123, 456]]
        for test in tests:
            # TypeError isn't caught unless you add the lambda
            self.assertRaises(TypeError, lambda:  f.set_profiling(test))

if __name__ == '__main__':
    unittest.main()
