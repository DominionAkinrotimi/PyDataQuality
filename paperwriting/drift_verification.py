import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pydataquality as pdq
from pydataquality.comparator import DataQualityComparator
import pandas as pd
import numpy as np
import json

np.random.seed(42)

# ─── Entropy verification ───────────────────────────────────────────────────
cats_skewed  = pd.Series(['A']*50 + ['B']*30 + ['C']*20)
cats_uniform = pd.Series(['A']*33 + ['B']*33 + ['C']*34)
cats_binary  = pd.Series(['Yes']*500 + ['No']*500)

def shanon_entropy(s):
    v = s.value_counts(normalize=True)
    return float(-np.sum(v * np.log2(v)))

print("=== Shannon Entropy Results ===")
print(f"Entropy 50/30/20 distribution: {shanon_entropy(cats_skewed):.6f} bits")
print(f"Entropy near-uniform 33/33/34: {shanon_entropy(cats_uniform):.6f} bits")
print(f"Binary entropy 50/50:          {shanon_entropy(cats_binary):.6f} bits")

# ─── IQR Demo ────────────────────────────────────────────────────────────────
data = pd.Series([10, 12, 14, 15, 16, 18, 20, 22, 100, 200])
Q1 = data.quantile(0.25)
Q3 = data.quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR
outliers = data[(data < lower) | (data > upper)]
print("\n=== IQR Outlier Detection ===")
print(f"Dataset: {data.tolist()}")
print(f"Q1={Q1}, Q3={Q3}, IQR={IQR}, Lower fence={lower:.2f}, Upper fence={upper:.2f}")
print(f"Outliers detected: {outliers.tolist()}")

# ─── PSI & KS Grid Test ──────────────────────────────────────────────────────
ref_data = pd.DataFrame({'score': np.random.normal(680, 50, 1000)})
curr_stable   = pd.DataFrame({'score': np.random.normal(682, 51, 500)})
curr_moderate = pd.DataFrame({'score': np.random.normal(620, 80, 500)})
curr_severe   = pd.DataFrame({'score': np.random.normal(560, 50, 500)})

ref_a  = pdq.analyze_dataframe(ref_data, name='Reference')
stab_a = pdq.analyze_dataframe(curr_stable, name='Stable')
mod_a  = pdq.analyze_dataframe(curr_moderate, name='Moderate')
sev_a  = pdq.analyze_dataframe(curr_severe, name='Severe')

c_stab = DataQualityComparator(ref_a, stab_a)
c_mod  = DataQualityComparator(ref_a, mod_a)
c_sev  = DataQualityComparator(ref_a, sev_a)

scenarios = [
    ('Stable (~2pt diff)',   c_stab),
    ('Moderate (~60pt diff)', c_mod),
    ('Severe (~120pt diff)',  c_sev),
]
print("\n=== PSI & KS Grid Results ===")
print(f"{'Scenario':<28} {'PSI':>10} {'Classification':>16} {'KS D-stat':>12} {'KS p-value':>14}")
print("-" * 85)
drift_grid = []
for name, comp in scenarios:
    psi = comp.calculate_psi('score')
    ks  = comp.calculate_ks('score')
    cls = 'stable' if psi < 0.1 else ('moderate' if psi < 0.25 else 'significant')
    print(f"{name:<28} {psi:>10.6f} {cls:>16} {ks['statistic']:>12.4f} {ks['p_value']:>14.6e}")
    drift_grid.append({'scenario': name, 'psi': psi, 'classification': cls,
                       'ks_statistic': ks['statistic'], 'ks_p_value': ks['p_value']})

# ─── get_problematic_rows Demo ───────────────────────────────────────────────
df_demo = pd.DataFrame({
    'age':    [25, 30, 28, -100, 27, 999, 32, 29, 31, 26, 28, 30],
    'income': [45000, 50000, None, 48000, 47000, 51000, None, 49000, 46000, 52000, 48500, 50500]
})
analyzer_demo = pdq.analyze_dataframe(df_demo, name='Demo')
prob_age_rows     = analyzer_demo.get_problematic_rows('age', 'outliers')
prob_income_rows  = analyzer_demo.get_problematic_rows('income', 'missing_values')
prob_all_rows     = analyzer_demo.get_problematic_rows('age', 'all')

print("\n=== get_problematic_rows Demo ===")
print(f"Total rows:               {len(df_demo)}")
print(f"Age outlier rows:         {len(prob_age_rows)}")
print(f"Income missing rows:      {len(prob_income_rows)}")
print(f"All issues (age col):     {len(prob_all_rows)}")
print("Problematic age rows (outliers):")
print(prob_age_rows.to_string())

# ─── Save results ────────────────────────────────────────────────────────────
results = {
    'entropy': {
        'skewed_50_30_20': shanon_entropy(cats_skewed),
        'near_uniform_33_33_34': shanon_entropy(cats_uniform),
        'binary_50_50': shanon_entropy(cats_binary),
    },
    'iqr_demo': {
        'Q1': Q1, 'Q3': Q3, 'IQR': IQR,
        'lower_fence': lower, 'upper_fence': upper,
        'outliers': outliers.tolist()
    },
    'drift_grid': drift_grid,
    'problematic_rows': {
        'total_rows': len(df_demo),
        'age_outlier_rows': len(prob_age_rows),
        'income_missing_rows': len(prob_income_rows),
    }
}

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'drift_verification_results.json')
with open(out_path, 'w') as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nResults saved to: {out_path}")
