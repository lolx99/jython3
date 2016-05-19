"""Misc inspect tests

Made for Jython.
"""
import inspect
import unittest
from java.lang import System
from test import support

class InspectTestCase(unittest.TestCase):

    def test_java_routine(self):
        self.assertTrue(inspect.isroutine(System.arraycopy))


def test_main():
    support.run_unittest(InspectTestCase)


if __name__ == '__main__':
    test_main()
