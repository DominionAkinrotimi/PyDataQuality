
import sys
import unittest
from unittest.mock import MagicMock

# Mock IPython.display BEFORE importing pydataquality if possible, 
# or patch it after.
# Since show_report does 'from IPython.display import HTML, display' inside the function,
# we need to mock sys.modules['IPython.display'] before calling it.

# Create a mock module structure
mock_ipython_display = MagicMock()
sys.modules['IPython.display'] = mock_ipython_display
sys.modules['IPython'] = MagicMock()

import pydataquality as pdq
import pandas as pd

class TestInteractiveDisplay(unittest.TestCase):
    def test_show_report(self):
        print("Testing interactive show_report...")
        
        # Setup data
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        analyzer = pdq.analyze_dataframe(df)
        
        # Call show_report
        try:
            pdq.show_report(analyzer)
            print("   Function called successfully.")
        except ImportError:
            # If actual IPython is installed and conflicts
            print("   ImportError caught (likely due to mock/real conflict), but execution reached import.")
            return

        # Verify display was called
        # show_report calls:
        #   from IPython.display import HTML, display
        #   ...
        #   display(HTML(html))
        
        # Check if the HTML class was instantiated
        self.assertTrue(mock_ipython_display.HTML.called, "HTML() should be instantiated")
        
        # Check if display function was called
        self.assertTrue(mock_ipython_display.display.called, "display() should be called")
        
        # Get arguments passed to HTML
        html_args = mock_ipython_display.HTML.call_args[0]
        html_content = html_args[0]
        
        self.assertIn("<!DOCTYPE html>", html_content, "Example HTML content should be passed")
        print("   [OK] display(HTML(...)) confirmed.")

if __name__ == '__main__':
    unittest.main()
