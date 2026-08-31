# -*- coding: utf-8 -*-
"""
Robustness check: repeat the synthetic MLOps case study (Section 5.2) across many
random seeds to see whether the Baseline -> Pipeline A accuracy drop reported in
Table 8 (a single seed=42 run) is a robust effect or an artifact of that one split.

This does NOT replace or alter Table 8 (which stays pinned to the paper's stated
reproducibility seeds). It produces an additional robustness statistic to cite
alongside it.
"""
import sys, json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

sys.path.insert(0, r"D:\Dominion\PyDataQualityRepo")
import pydataquality as pdq

def generate_base_data(rows=5000, seed=42):
    np.random.seed(seed)
    credit_score = np.random.normal(680, 50, rows)
    income = np.random.normal(55000, 12000, rows)
    age = np.random.normal(38, 10, rows)
    debt_ratio = np.random.uniform(0.1, 0.6, rows)
    credit_score = np.clip(credit_score, 300, 850)
    income = np.clip(income, 10000, 150000)
    age = np.clip(age, 18, 80)
    score = (credit_score - 500)/350 * 0.4 + (income - 10000)/140000 * 0.4 - (debt_ratio - 0.1)/0.5 * 0.2
    approval_prob = 1 / (1 + np.exp(-10 * (score - 0.2)))
    approved = (np.random.rand(rows) < approval_prob).astype(int)
    return pd.DataFrame({
        'credit_score': credit_score, 'income': income, 'age': age,
        'debt_ratio': debt_ratio, 'approved': approved
    })

def generate_corrupted_test_data(rows=1000, seed=100):
    np.random.seed(seed)
    df = generate_base_data(rows, seed)
    mask_missing = np.random.rand(rows) < 0.15
    df.loc[mask_missing, 'income'] = np.nan
    mask_outlier_age = np.random.rand(rows) < 0.05
    df.loc[mask_outlier_age, 'age'] = np.random.choice([-100, 999], size=sum(mask_outlier_age))
    df['credit_score'] = df['credit_score'] - 120
    df['credit_score'] = np.clip(df['credit_score'], 300, 850)
    return df

N_TRIALS = 30
FEATURES = ['credit_score', 'income', 'age', 'debt_ratio']

# Fixed underlying trained population (matches the paper's canonical seed=42 setup) -
# only the split, the model fit, and the corrupted test batch vary across trials.
df_train = generate_base_data(rows=5000, seed=42)
X_full = df_train[FEATURES]
y_full = df_train['approved']

rows = []
for trial in range(N_TRIALS):
    split_seed = 1000 + trial
    model_seed = 1000 + trial
    corrupt_seed = 2000 + trial

    X_train, X_val, y_train, y_val = train_test_split(
        X_full, y_full, test_size=0.2, random_state=split_seed)
    model = RandomForestClassifier(n_estimators=100, random_state=model_seed)
    model.fit(X_train, y_train)

    y_val_pred = model.predict(X_val)
    baseline = dict(
        accuracy=accuracy_score(y_val, y_val_pred),
        precision=precision_score(y_val, y_val_pred),
        recall=recall_score(y_val, y_val_pred),
        f1=f1_score(y_val, y_val_pred),
    )

    df_test_dirty = generate_corrupted_test_data(rows=1000, seed=corrupt_seed)
    X_test_dirty = df_test_dirty[FEATURES].copy()
    y_test = df_test_dirty['approved']

    # Pipeline A - blind median fill only
    X_a = X_test_dirty.copy()
    X_a['income'] = X_a['income'].fillna(df_train['income'].median())
    y_pred_a = model.predict(X_a)
    pipeline_a = dict(
        accuracy=accuracy_score(y_test, y_pred_a),
        precision=precision_score(y_test, y_pred_a),
        recall=recall_score(y_test, y_pred_a),
        f1=f1_score(y_test, y_pred_a),
    )

    # Pipeline B - PyDataQuality gate
    train_analyzer = pdq.analyze_dataframe(df_train, name="Train_Baseline")
    test_analyzer = pdq.analyze_dataframe(df_test_dirty, name="Test_Production")
    drift_df = pdq.compare_drift(train_analyzer, test_analyzer)
    credit_psi = float(drift_df.loc[drift_df['column'] == 'credit_score', 'psi'].iloc[0])

    X_b = X_test_dirty.copy()
    X_b['income'] = X_b['income'].fillna(df_train['income'].median())
    age_stats = train_analyzer.column_stats['age'].stats
    q1, q3 = age_stats['q1'], age_stats['q3']
    iqr = q3 - q1
    X_b['age'] = X_b['age'].clip(lower=q1 - 1.5*iqr, upper=q3 + 1.5*iqr)
    y_pred_b = model.predict(X_b)
    pipeline_b = dict(
        accuracy=accuracy_score(y_test, y_pred_b),
        precision=precision_score(y_test, y_pred_b),
        recall=recall_score(y_test, y_pred_b),
        f1=f1_score(y_test, y_pred_b),
    )

    rows.append(dict(
        trial=trial,
        baseline_acc=baseline['accuracy'], pipeline_a_acc=pipeline_a['accuracy'], pipeline_b_acc=pipeline_b['accuracy'],
        baseline_f1=baseline['f1'], pipeline_a_f1=pipeline_a['f1'], pipeline_b_f1=pipeline_b['f1'],
        drop_pp=(baseline['accuracy'] - pipeline_a['accuracy']) * 100,
        credit_score_psi=credit_psi,
    ))
    print(f"trial {trial}: baseline_acc={baseline['accuracy']:.4f} pipeline_a_acc={pipeline_a['accuracy']:.4f} "
          f"drop_pp={rows[-1]['drop_pp']:.2f} psi={credit_psi:.3f}")

df_res = pd.DataFrame(rows)
summary = {
    'n_trials': N_TRIALS,
    'baseline_acc_mean': df_res['baseline_acc'].mean(), 'baseline_acc_std': df_res['baseline_acc'].std(),
    'pipeline_a_acc_mean': df_res['pipeline_a_acc'].mean(), 'pipeline_a_acc_std': df_res['pipeline_a_acc'].std(),
    'pipeline_b_acc_mean': df_res['pipeline_b_acc'].mean(), 'pipeline_b_acc_std': df_res['pipeline_b_acc'].std(),
    'drop_pp_mean': df_res['drop_pp'].mean(), 'drop_pp_std': df_res['drop_pp'].std(),
    'drop_pp_min': df_res['drop_pp'].min(), 'drop_pp_max': df_res['drop_pp'].max(),
    'trials_with_drop': int((df_res['drop_pp'] > 0).sum()),
    'credit_score_psi_mean': df_res['credit_score_psi'].mean(), 'credit_score_psi_std': df_res['credit_score_psi'].std(),
    'credit_score_psi_min': df_res['credit_score_psi'].min(),
}
print()
print(json.dumps(summary, indent=2))

df_res.to_csv('repeated_trials_raw.csv', index=False)
with open('repeated_trials_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)
print("\nSaved repeated_trials_raw.csv and repeated_trials_summary.json")
