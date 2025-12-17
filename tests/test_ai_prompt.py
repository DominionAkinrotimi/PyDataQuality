import unittest
import pandas as pd
import numpy as np
from pydataquality.analyzer import DataQualityAnalyzer
from pydataquality.reporter import QualityReportGenerator

class TestAIPrompt(unittest.TestCase):
    def setUp(self):
        # Create a dataset with known issues
        self.df = pd.DataFrame({
            'age': [25, 26, 25, 24, 25, 150, -5, 25, 26, 25],  # Outliers
            'email': ['a@b.com'] * 8 + [np.nan, np.nan],       # Missing
            'category': ['A'] * 8 + ['B', 'C']                 # Categorical
        })
        self.analyzer = DataQualityAnalyzer(self.df, name="Test Data")
        self.reporter = QualityReportGenerator(self.analyzer)

    def test_prompt_includes_details(self):
        """Test that the prompt includes specific details like ranges and percentages."""
        prompt = self.reporter.generate_ai_remediation_prompt(include_eda=False)
        
        # Check outliers detail
        self.assertIn("age (outliers", prompt)
        self.assertIn("outside [", prompt)
        
        # Check missing values detail
        self.assertIn("email (missing_values", prompt)
        self.assertIn("% missing", prompt)

    def test_prompt_includes_eda(self):
        """Test that the prompt includes EDA statistics when requested."""
        prompt = self.reporter.generate_ai_remediation_prompt(include_eda=True)
        
        # Check for EDA section header
        self.assertIn("statistical context (EDA)", prompt)
        
        # Check numeric stats
        self.assertIn("Mean=", prompt)
        self.assertIn("Max=150.00", prompt)
        
        # Check categorical stats
        self.assertIn("Unique Values=", prompt)
        self.assertIn("Top Value=", prompt)
        
    def test_prompt_no_eda(self):
        """Test that EDA context is omitted when include_eda=False."""
        prompt = self.reporter.generate_ai_remediation_prompt(include_eda=False)
        self.assertNotIn("statistical context (EDA)", prompt)

if __name__ == '__main__':
    unittest.main()
