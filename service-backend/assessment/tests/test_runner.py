# service-backend/assessment/tests/test_runner.py
import unittest
import os
import importlib
import traceback
from django.test import TestCase

def discover_tests():
    """
    Discovers all tests in the assessment/tests directory.
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

class CustomTestResult(unittest.TestResult):
    """
    A custom test result class to capture test outcomes as they happen.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.results.append({
            'test': str(test),
            'result': 'PASS',
            'error': ''
        })

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.results.append({
            'test': str(test),
            'result': 'FAIL',
            'error': f"Failure: {self._exc_info_to_string(err, test)}"
        })

    def addError(self, test, err):
        super().addError(test, err)
        self.results.append({
            'test': str(test),
            'result': 'FAIL',
            'error': f"Error: {self._exc_info_to_string(err, test)}"
        })

def run_tests(test_path=None):
    """
    Runs either all discovered tests or a specific test using a custom result collector.
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
        tests_dir = os.path.dirname(__file__)
        suite = loader.discover(tests_dir, pattern='test_*.py')

    # Create an instance of our custom result collector
    result = CustomTestResult()

    # Run the suite with the custom result object
    suite.run(result)

    return result.results
