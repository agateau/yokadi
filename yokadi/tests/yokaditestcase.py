"""
Yokadi base class for test cases
@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or later
"""
import os
import shutil
import tempfile
import unittest

from yokadi.tests.testutils import EnvironSaver


class YokadiTestCase(unittest.TestCase):
    """
    A TestCase which takes care of isolating the test from the user home dir
    and environment.
    """
    def setUp(self):
        self.__envSaver = EnvironSaver()
        self.testHomeDir = tempfile.mkdtemp(prefix="yokadi-basepaths-testcase")
        os.environ["HOME"] = self.testHomeDir
        os.environ["XDG_DATA_HOME"] = ""
        os.environ["XDG_CACHE_HOME"] = ""
        os.environ["YOKADI_DB"] = ""
        os.environ["YOKADI_HISTORY"] = ""
        self.__cwd = os.getcwd()

    def tearDown(self):
        shutil.rmtree(self.testHomeDir)
        self.__envSaver.restore()
        os.chdir(self.__cwd)
