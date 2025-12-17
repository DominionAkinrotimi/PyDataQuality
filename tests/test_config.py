import pytest
import pandas as pd
import numpy as np
import pydataquality as pdq

def test_config_override():
    """Test that custom configuration overrides default thresholds."""
    df = pd.DataFrame({
        'col1': [1, 2, np.nan, np.nan], # 50% missing
    })
    
    # Default behavior: 50% missing is critical (threshold 0.3)
    analyzer_default = pdq.analyze_dataframe(df, "Default")
    issues_default = [i for i in analyzer_default.issues if i.column == 'col1']
    assert len(issues_default) > 0
    assert issues_default[0].severity == 'critical'
    
    # Custom behavior: Set critical threshold to 0.6 (60%)
    # So 50% missing should NOT be critical (it might be warning or OK)
    custom_config = {'missing_critical': 0.6}
    analyzer_custom = pdq.analyze_dataframe(df, "Custom", config=custom_config)
    
    issues_custom = [i for i in analyzer_custom.issues if i.column == 'col1' and i.severity == 'critical']
    assert len(issues_custom) == 0, "Should not be critical with relaxed threshold"

if __name__ == "__main__":
    pytest.main([__file__])
