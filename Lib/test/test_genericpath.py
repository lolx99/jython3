"""
Tests common to genericpath, macpath, ntpath and posixpath
"""

import unittest
from test import support
import os
import genericpath
import sys


def safe_rmdir(dirname):
    try:
        os.rmdir(dirname)
    except OSError:
        pass


class GenericTest(unittest.TestCase):
    # The path module to be tested
    pathmodule = genericpath
    common_attributes = ['commonprefix', 'getsize', 'getatime', 'getctime',
                         'getmtime', 'exists', 'isdir', 'isfile']
    attributes = []

    def test_no_argument(self):
        for attr in self.common_attributes + self.attributes:
            with self.assertRaises(TypeError):
                getattr(self.pathmodule, attr)()
                raise self.fail("{}.{}() did not raise a TypeError"
                                .format(self.pathmodule.__name__, attr))

    def test_commonprefix(self):
        commonprefix = self.pathmodule.commonprefix
        self.assertEqual(
            commonprefix([]),
            ""
        )
        self.assertEqual(
            commonprefix(["/home/swenson/spam", "/home/swen/spam"]),
            "/home/swen"
        )
        self.assertEqual(
            commonprefix(["/home/swen/spam", "/home/swen/eggs"]),
            "/home/swen/"
        )
        self.assertEqual(
            commonprefix(["/home/swen/spam", "/home/swen/spam"]),
            "/home/swen/spam"
        )
        self.assertEqual(
            commonprefix(["home:swenson:spam", "home:swen:spam"]),
            "home:swen"
        )
        self.assertEqual(
            commonprefix([":home:swen:spam", ":home:swen:eggs"]),
            ":home:swen:"
        )
        self.assertEqual(
            commonprefix([":home:swen:spam", ":home:swen:spam"]),
            ":home:swen:spam"
        )

        testlist = ['', 'abc', 'Xbcd', 'Xb', 'XY', 'abcd',
                    'aXc', 'abd', 'ab', 'aX', 'abcX']
        for s1 in testlist:
            for s2 in testlist:
                p = commonprefix([s1, s2])
                self.assertTrue(s1.startswith(p))
                self.assertTrue(s2.startswith(p))
                if s1 != s2:
                    n = len(p)
                    self.assertNotEqual(s1[n:n+1], s2[n:n+1])

    def test_getsize(self):
        f = open(support.TESTFN, "wb")
        try:
            f.write("foo")
            f.close()
            self.assertEqual(self.pathmodule.getsize(support.TESTFN), 3)
        finally:
            if not f.closed:
                f.close()
            support.unlink(support.TESTFN)

    def test_time(self):
        f = open(support.TESTFN, "wb")
        try:
            f.write("foo")
            f.close()
            f = open(support.TESTFN, "ab")
            f.write("bar")
            f.close()
            f = open(support.TESTFN, "rb")
            d = f.read()
            f.close()
            self.assertEqual(d, "foobar")

            self.assertLessEqual(
                self.pathmodule.getctime(support.TESTFN),
                self.pathmodule.getmtime(support.TESTFN)
            )
        finally:
            if not f.closed:
                f.close()
            support.unlink(support.TESTFN)

    def test_exists(self):
        self.assertIs(self.pathmodule.exists(support.TESTFN), False)
        f = open(support.TESTFN, "wb")
        try:
            f.write("foo")
            f.close()
            self.assertIs(self.pathmodule.exists(support.TESTFN), True)
            if not self.pathmodule == genericpath:
                self.assertIs(self.pathmodule.lexists(support.TESTFN),
                              True)
        finally:
            if not f.close():
                f.close()
            support.unlink(support.TESTFN)

    def test_isdir(self):
        self.assertIs(self.pathmodule.isdir(support.TESTFN), False)
        f = open(support.TESTFN, "wb")
        try:
            f.write("foo")
            f.close()
            self.assertIs(self.pathmodule.isdir(support.TESTFN), False)
            os.remove(support.TESTFN)
            os.mkdir(support.TESTFN)
            self.assertIs(self.pathmodule.isdir(support.TESTFN), True)
            os.rmdir(support.TESTFN)
        finally:
            if not f.close():
                f.close()
            support.unlink(support.TESTFN)
            safe_rmdir(support.TESTFN)

    def test_isfile(self):
        self.assertIs(self.pathmodule.isfile(support.TESTFN), False)
        f = open(support.TESTFN, "wb")
        try:
            f.write("foo")
            f.close()
            self.assertIs(self.pathmodule.isfile(support.TESTFN), True)
            os.remove(support.TESTFN)
            os.mkdir(support.TESTFN)
            self.assertIs(self.pathmodule.isfile(support.TESTFN), False)
            os.rmdir(support.TESTFN)
        finally:
            if not f.close():
                f.close()
            support.unlink(support.TESTFN)
            safe_rmdir(support.TESTFN)


# Following TestCase is not supposed to be run from test_genericpath.
# It is inherited by other test modules (macpath, ntpath, posixpath).

class CommonTest(GenericTest):
    # The path module to be tested
    pathmodule = None
    common_attributes = GenericTest.common_attributes + [
        # Properties
        'curdir', 'pardir', 'extsep', 'sep',
        'pathsep', 'defpath', 'altsep', 'devnull',
        # Methods
        'normcase', 'splitdrive', 'expandvars', 'normpath', 'abspath',
        'join', 'split', 'splitext', 'isabs', 'basename', 'dirname',
        'lexists', 'islink', 'ismount', 'expanduser', 'normpath', 'realpath',
    ]

    def test_normcase(self):
        # Check that normcase() is idempotent
        p = "FoO/./BaR"
        p = self.pathmodule.normcase(p)
        self.assertEqual(p, self.pathmodule.normcase(p))

    def test_splitdrive(self):
        # splitdrive for non-NT paths
        splitdrive = self.pathmodule.splitdrive
        self.assertEqual(splitdrive("/foo/bar"), ("", "/foo/bar"))
        self.assertEqual(splitdrive("foo:bar"), ("", "foo:bar"))
        self.assertEqual(splitdrive(":foo:bar"), ("", ":foo:bar"))

    def test_expandvars(self):
        if self.pathmodule.__name__ == 'macpath':
            self.skipTest('macpath.expandvars is a stub')
        expandvars = self.pathmodule.expandvars
        with support.EnvironmentVarGuard() as env:
            env.clear()
            env["foo"] = "bar"
            env["{foo"] = "baz1"
            env["{foo}"] = "baz2"
            self.assertEqual(expandvars("foo"), "foo")
            self.assertEqual(expandvars("$foo bar"), "bar bar")
            self.assertEqual(expandvars("${foo}bar"), "barbar")
            self.assertEqual(expandvars("$[foo]bar"), "$[foo]bar")
            self.assertEqual(expandvars("$bar bar"), "$bar bar")
            self.assertEqual(expandvars("$?bar"), "$?bar")
            self.assertEqual(expandvars("${foo}bar"), "barbar")
            self.assertEqual(expandvars("$foo}bar"), "bar}bar")
            self.assertEqual(expandvars("${foo"), "${foo")
            self.assertEqual(expandvars("${{foo}}"), "baz1}")
            self.assertEqual(expandvars("$foo$foo"), "barbar")
            self.assertEqual(expandvars("$bar$bar"), "$bar$bar")

    def test_abspath(self):
        self.assertIn("foo", self.pathmodule.abspath("foo"))

        # Abspath returns bytes when the arg is bytes
        for path in ('', 'foo', 'f\xf2\xf2', '/foo', 'C:\\'):
            self.assertIsInstance(self.pathmodule.abspath(path), str)

    def test_realpath(self):
        self.assertIn("foo", self.pathmodule.realpath("foo"))

    def test_normpath_issue5827(self):
        # Make sure normpath preserves unicode
        for path in ('', '.', '/', '\\', '///foo/.//bar//'):
            self.assertIsInstance(self.pathmodule.normpath(path), str)

    def test_abspath_issue3426(self):
        # Check that abspath returns unicode when the arg is unicode
        # with both ASCII and non-ASCII cwds.
        abspath = self.pathmodule.abspath
        for path in ('', 'fuu', 'f\xf9\xf9', '/fuu', 'U:\\'):
            self.assertIsInstance(abspath(path), str)

        unicwd = '\xe7w\xf0'
        try:
            fsencoding = support.TESTFN_ENCODING or "ascii"
            unicwd.encode(fsencoding)
        except (AttributeError, UnicodeEncodeError):
            # FS encoding is probably ASCII
            pass
        else:
            with support.temp_cwd(unicwd):
                for path in ('', 'fuu', 'f\xf9\xf9', '/fuu', 'U:\\'):
                    self.assertIsInstance(abspath(path), str)

    @unittest.skipIf(sys.platform == 'darwin' or support.is_jython,
        "Both Mac OS X and Java deny the creation of a directory with an invalid utf8 name")
    def test_nonascii_abspath(self):
        # Test non-ASCII, non-UTF8 bytes in the path.
        with support.temp_cwd('\xe7w\xf0'):
            self.test_abspath()


def test_main():
    support.run_unittest(GenericTest)


if __name__=="__main__":
    test_main()
