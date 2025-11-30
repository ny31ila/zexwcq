# service-backend/assessment/tests/test_runner.py
import unittest
import os
import importlib
import traceback
from django.test import TestCase

def discover_tests():
    """
    Discovers all tests in the assessment/tests directory.

    Returns:
        A list of dictionaries, where each dictionary represents a test method
        and contains 'module', 'class', and 'method' keys.
    """
    tests = []
    tests_dir = os.path.dirname(__file__)

    for filename in os.listdir(tests_dir):
        if filename.startswith('test_') and filename.endswith('.py'):
            module_name = f"assessment.tests.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                for name in dir(module):
                    obj = getattr(module, name)
                    if isinstance(obj, type) and issubclass(obj, TestCase):
                        for method_name in dir(obj):
                            if method_name.startswith('test_'):
                                tests.append({
                                    'module': module_name,
                                    'class': name,
                                    'method': method_name,
                                    'full_path': f"{module_name}.{name}.{method_name}"
                                })
            except ImportError:
                continue
    return sorted(tests, key=lambda x: x['full_path'])

def run_tests(test_path=None):
    """
    Runs either all discovered tests or a specific test.

    Args:
        test_path (str, optional): The full path to a specific test to run,
                                   e.g., 'assessment.tests.test_services.SwansonAssessmentScoringTest.test_combined'.
                                   If None, all tests are run.

    Returns:
        A list of dictionaries, where each dictionary contains the test path
        and its result ('PASS', 'FAIL'), along with an error message if it failed.
    """
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    if test_path:
        try:
            suite.addTest(loader.loadTestsFromName(test_path))
        except (ImportError, AttributeError):
            return [{
                'test': test_path,
                'result': 'FAIL',
                'error': f"Test path '{test_path}' not found or could not be loaded."
            }]
    else:
        # Discover all tests in the current directory (assessment.tests)
        tests_dir = os.path.dirname(__file__)
        suite = loader.discover(tests_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=0, failfast=False, buffer=True)
    result = runner.run(suite)

    results = []

    for test, _ in result.successes:
        results.append({
            'test': str(test),
            'result': 'PASS',
            'error': ''
        })

    for test, err in result.failures:
        results.append({
            'test': str(test),
            'result': 'FAIL',
            'error': f"Failure: {err}"
        })

    for test, err in result.errors:
        results.append({
            'test': str(test),
            'result': 'FAIL',
            'error': f"Error: {err}"
        })

    return results
