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

# ─── PSI Bin Sensitivity (Skewed Data) ───────────────────────────────────────
print("\n=== PSI Bin Sensitivity on Skewed Data ===")
# Generate a highly skewed (power-law) distribution
ref_skewed = pd.DataFrame({'value': np.random.pareto(a=2, size=1000) * 100})
# A slight shift in the tail, but mostly similar
curr_skewed = pd.DataFrame({'value': np.random.pareto(a=1.8, size=1000) * 100})

a_ref_skewed = pdq.analyze_dataframe(ref_skewed, name='Ref_Skewed')
a_curr_skewed = pdq.analyze_dataframe(curr_skewed, name='Curr_Skewed')

comp_skewed = DataQualityComparator(a_ref_skewed, a_curr_skewed)
psi_skewed = comp_skewed.calculate_psi('value')
ks_skewed = comp_skewed.calculate_ks('value')

print(f"Skewed Data PSI: {psi_skewed:.6f}")
print(f"Skewed Data KS : {ks_skewed['statistic']:.4f} (p={ks_skewed['p_value']:.2e})")
print("Note: PSI may exhibit high sensitivity (false positives or calculation artifacts) on highly skewed data due to binning instability.")


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
    'psi_skewed_sensitivity': {
        'psi': psi_skewed,
        'ks_statistic': ks_skewed['statistic'],
        'ks_p_value': ks_skewed['p_value']
    },
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
