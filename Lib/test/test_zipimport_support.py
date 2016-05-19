# This test module covers support in various parts of the standard library
# for working with modules located inside zipfiles
# The tests are centralised in this fashion to make it easy to drop them
# if a platform doesn't support zipimport
import test.support
from test.support import is_jython
import unittest
import os
import os.path
import sys
import textwrap
import zipfile
import zipimport
import doctest
import inspect
import linecache
import pdb
import warnings
from test.script_helper import (spawn_python, kill_python, run_python,
                                temp_dir, make_script, make_zip_script)

verbose = test.support.verbose

# Library modules covered by this test set
#  pdb (Issue 4201)
#  inspect (Issue 4223)
#  doctest (Issue 4197)

# Other test modules with zipimport related tests
#  test_zipimport (of course!)
#  test_cmd_line_script (covers the zipimport support in runpy)

# Retrieve some helpers from other test cases
from test import (test_doctest, sample_doctest, sample_doctest_no_doctests,
                  sample_doctest_no_docstrings)
from test.test_importhooks import ImportHooksBaseTestCase

if is_jython and os._name=="nt":
    # Jython holds open zip/jar files placed on its sys.path. (Assume there
    # is a good reason for this.) Windows will not then allow the script
    # directory to be cleaned up on context exit, resulting in test failures
    # unrelated to the purpose of the test.

    # Replace test.script_helper.temp_dir with this copy.
    import contextlib, tempfile, shutil, warnings
    @contextlib.contextmanager
    def temp_dir():
        dirname = os.path.realpath(tempfile.mkdtemp())
        try:
            yield dirname
        finally:
            try:
                shutil.rmtree(dirname)
            except OSError:
                warnings.warn("Failed to remove "+dirname)

def _run_object_doctest(obj, module):
    # Direct doctest output (normally just errors) to real stdout; doctest
    # output shouldn't be compared by regrtest.
    save_stdout = sys.stdout
    sys.stdout = test.support.get_original_stdout()
    try:
        finder = doctest.DocTestFinder(verbose=verbose, recurse=False)
        runner = doctest.DocTestRunner(verbose=verbose)
        # Use the object's fully qualified name if it has one
        # Otherwise, use the module's name
        try:
            name = "%s.%s" % (obj.__module__, obj.__name__)
        except AttributeError:
            name = module.__name__
        for example in finder.find(obj, name, module):
            runner.run(example)
        f, t = runner.failures, runner.tries
        if f:
            raise test.support.TestFailed("%d of %d doctests failed" % (f, t))
    finally:
        sys.stdout = save_stdout
    if verbose:
        print('doctest (%s) ... %d tests with zero failures' % (module.__name__, t))
    return f, t



class ZipSupportTests(ImportHooksBaseTestCase):
    # We use the ImportHooksBaseTestCase to restore
    # the state of the import related information
    # in the sys module after each test
    # We also clear the linecache and zipimport cache
    # just to avoid any bogus errors due to name reuse in the tests
    def setUp(self):
        linecache.clearcache()
        zipimport._zip_directory_cache.clear()
        ImportHooksBaseTestCase.setUp(self)


    def test_inspect_getsource_issue4223(self):
        test_src = "def foo(): pass\n"
        with temp_dir() as d:
            init_name = make_script(d, '__init__', test_src)
            name_in_zip = os.path.join('zip_pkg',
                                       os.path.basename(init_name))
            zip_name, run_name = make_zip_script(d, 'test_zip',
                                                init_name, name_in_zip)
            os.remove(init_name)
            sys.path.insert(0, zip_name)
            import zip_pkg
            self.assertEqual(inspect.getsource(zip_pkg.foo), test_src)

    def test_doctest_issue4197(self):
        # To avoid having to keep two copies of the doctest module's
        # unit tests in sync, this test works by taking the source of
        # test_doctest itself, rewriting it a bit to cope with a new
        # location, and then throwing it in a zip file to make sure
        # everything still works correctly
        test_src = inspect.getsource(test_doctest)
        test_src = test_src.replace(
                         "from test import test_doctest",
                         "import test_zipped_doctest as test_doctest")
        test_src = test_src.replace("test.test_doctest",
                                    "test_zipped_doctest")
        test_src = test_src.replace("test.sample_doctest",
                                    "sample_zipped_doctest")
        # The sample doctest files rewritten to include in the zipped version.
        sample_sources = {}
        for mod in [sample_doctest, sample_doctest_no_doctests,
                    sample_doctest_no_docstrings]:
            src = inspect.getsource(mod)
            src = src.replace("test.test_doctest", "test_zipped_doctest")
            # Rewrite the module name so that, for example,
            # "test.sample_doctest" becomes "sample_zipped_doctest".
            mod_name = mod.__name__.split(".")[-1]
            mod_name = mod_name.replace("sample_", "sample_zipped_")
            sample_sources[mod_name] = src

        with temp_dir() as d:
            script_name = make_script(d, 'test_zipped_doctest',
                                            test_src)
            zip_name, run_name = make_zip_script(d, 'test_zip',
                                                script_name)
            z = zipfile.ZipFile(zip_name, 'a')
            for mod_name, src in list(sample_sources.items()):
                z.writestr(mod_name + ".py", src)
            z.close()
            if verbose:
                zip_file = zipfile.ZipFile(zip_name, 'r')
                print('Contents of %r:' % zip_name)
                zip_file.printdir()
                zip_file.close()
            os.remove(script_name)
            sys.path.insert(0, zip_name)
            import test_zipped_doctest
            # Some of the doc tests depend on the colocated text files
            # which aren't available to the zipped version (the doctest
            # module currently requires real filenames for non-embedded
            # tests). So we're forced to be selective about which tests
            # to run.
            # doctest could really use some APIs which take a text
            # string or a file object instead of a filename...
            known_good_tests = [
                test_zipped_doctest.SampleClass,
                test_zipped_doctest.SampleClass.NestedClass,
                test_zipped_doctest.SampleClass.NestedClass.__init__,
                test_zipped_doctest.SampleClass.__init__,
                test_zipped_doctest.SampleClass.a_classmethod,
                test_zipped_doctest.SampleClass.a_property,
                test_zipped_doctest.SampleClass.a_staticmethod,
                test_zipped_doctest.SampleClass.double,
                test_zipped_doctest.SampleClass.get,
                test_zipped_doctest.SampleNewStyleClass,
                test_zipped_doctest.SampleNewStyleClass.__init__,
                test_zipped_doctest.SampleNewStyleClass.double,
                test_zipped_doctest.SampleNewStyleClass.get,
                test_zipped_doctest.old_test1,
                test_zipped_doctest.old_test2,
                test_zipped_doctest.old_test3,
                test_zipped_doctest.old_test4,
                test_zipped_doctest.sample_func,
                test_zipped_doctest.test_DocTest,
                test_zipped_doctest.test_DocTestParser,
                test_zipped_doctest.test_DocTestRunner.basics,
                test_zipped_doctest.test_DocTestRunner.exceptions,
                test_zipped_doctest.test_DocTestRunner.option_directives,
                test_zipped_doctest.test_DocTestRunner.optionflags,
                test_zipped_doctest.test_DocTestRunner.verbose_flag,
                test_zipped_doctest.test_Example,
                test_zipped_doctest.test_debug,
                test_zipped_doctest.test_pdb_set_trace,
                test_zipped_doctest.test_pdb_set_trace_nested,
                test_zipped_doctest.test_testsource,
                test_zipped_doctest.test_trailing_space_in_test,
                test_zipped_doctest.test_DocTestSuite,
                test_zipped_doctest.test_DocTestFinder,
            ]
            # These remaining tests are the ones which need access
            # to the data files, so we don't run them
            fail_due_to_missing_data_files = [
                test_zipped_doctest.test_DocFileSuite,
                test_zipped_doctest.test_testfile,
                test_zipped_doctest.test_unittest_reportflags,
            ]
            # Needed for test_DocTestParser and test_debug
            deprecations = []
            if __debug__:
                # Ignore all warnings about the use of class Tester in this module.
                deprecations.append(("class Tester is deprecated", DeprecationWarning))
            if sys.py3kwarning:
                deprecations += [
                    ("backquote not supported", SyntaxWarning),
                    ("execfile.. not supported", DeprecationWarning)]
            with test.support.check_warnings(*deprecations):
                for obj in known_good_tests:
                    _run_object_doctest(obj, test_zipped_doctest)

    def test_doctest_main_issue4197(self):
        test_src = textwrap.dedent("""\
                    class Test:
                        ">>> 'line 2'"
                        pass

                    import doctest
                    doctest.testmod()
                    """)
        pattern = 'File "%s", line 2, in %s'
        with temp_dir() as d:
            script_name = make_script(d, 'script', test_src)
            exit_code, data = run_python(script_name)
            expected = pattern % (script_name, "__main__.Test")
            if verbose:
                print("Expected line", expected)
                print("Got stdout:")
                print(data)
            self.assertIn(expected, data)
            zip_name, run_name = make_zip_script(d, "test_zip",
                                                script_name, '__main__.py')
            exit_code, data = run_python(zip_name)
            expected = pattern % (run_name, "__main__.Test")
            if verbose:
                print("Expected line", expected)
                print("Got stdout:")
                print(data)
            self.assertIn(expected, data)

    def test_pdb_issue4201(self):
        test_src = textwrap.dedent("""\
                    def f():
                        pass

                    import pdb
                    pdb.runcall(f)
                    """)
        with temp_dir() as d:
            script_name = make_script(d, 'script', test_src)
            p = spawn_python(script_name)
            p.stdin.write('l\n')
            data = kill_python(p)
            # bdb/pdb applies normcase to its filename before displaying
            # See CPython Issue 14255 (back-ported for Jython)
            self.assertIn(os.path.normcase(script_name.encode('utf-8')), data)
            zip_name, run_name = make_zip_script(d, "test_zip",
                                                script_name, '__main__.py')
            p = spawn_python(zip_name)
            p.stdin.write('l\n')
            data = kill_python(p)
            # bdb/pdb applies normcase to its filename before displaying
            # See CPython Issue 14255 (back-ported for Jython)
            self.assertIn(os.path.normcase(run_name.encode('utf-8')), data)


def test_main():
    test.support.run_unittest(ZipSupportTests)
    test.support.reap_children()

if __name__ == '__main__':
    test_main()
