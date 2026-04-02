import sys
from unittest.mock import MagicMock

# Mock pandas and numpy before they're imported
sys.modules['pandas'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['streamlit'] = MagicMock()
sys.modules['pdfplumber'] = MagicMock()

import unittest
import test_dates
import test_pdf_reader

def run_tests():
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(test_dates))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(test_pdf_reader))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == '__main__':
    run_tests()
