import time
import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pydataquality as pdq

def generate_base_data(rows=5000, seed=42):
    """Generate clean training data for bank loan approval prediction."""
    np.random.seed(seed)
    
    credit_score = np.random.normal(680, 50, rows)
    income = np.random.normal(55000, 12000, rows)
    age = np.random.normal(38, 10, rows)
    debt_ratio = np.random.uniform(0.1, 0.6, rows)
    
    # Clip parameters to valid ranges
    credit_score = np.clip(credit_score, 300, 850)
    income = np.clip(income, 10000, 150000)
    age = np.clip(age, 18, 80)
    
    # Logic for approval (ground truth label)
    # Higher credit, higher income, lower debt ratio = higher approval probability
    score = (credit_score - 500)/350 * 0.4 + (income - 10000)/140000 * 0.4 - (debt_ratio - 0.1)/0.5 * 0.2
    approval_prob = 1 / (1 + np.exp(-10 * (score - 0.2)))
    approved = (np.random.rand(rows) < approval_prob).astype(int)
    
    df = pd.DataFrame({
        'credit_score': credit_score,
        'income': income,
        'age': age,
        'debt_ratio': debt_ratio,
        'approved': approved
    })
    return df

def generate_corrupted_test_data(rows=1000, seed=100):
    """Generate drifted and corrupted test data to simulate pipeline ingestion failures."""
    np.random.seed(seed)
    df = generate_base_data(rows, seed)
    
    # 1. Inject missing values (15% missing in income)
    mask_missing = np.random.rand(rows) < 0.15
    df.loc[mask_missing, 'income'] = np.nan
    
    # 2. Introduce severe outlier anomalies (impossible age entries)
    mask_outlier_age = np.random.rand(rows) < 0.05
    df.loc[mask_outlier_age, 'age'] = np.random.choice([-100, 999], size=sum(mask_outlier_age))
    
    # 3. Simulate severe distribution drift (economic credit score drop)
    # The average credit score drops by 120 points (e.g., severe credit crunch)
    df['credit_score'] = df['credit_score'] - 120
    df['credit_score'] = np.clip(df['credit_score'], 300, 850)
    
    return df

def run_ml_case_study():
    print("Running MLOps validation case study...")
    
    # Step A: Load base training data and train the classifier
    df_train = generate_base_data(rows=5000, seed=42)
    X = df_train[['credit_score', 'income', 'age', 'debt_ratio']]
    y = df_train['approved']
    
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Baseline validation evaluation
    y_val_pred = model.predict(X_val)
    baseline_metrics = {
        'accuracy': accuracy_score(y_val, y_val_pred),
        'precision': precision_score(y_val, y_val_pred),
        'recall': recall_score(y_val, y_val_pred),
        'f1': f1_score(y_val, y_val_pred)
    }
    print(f"   [Baseline Accuracy]: {baseline_metrics['accuracy']:.4f}")
    
    # Step B: Load drifted/corrupted test data
    df_test_dirty = generate_corrupted_test_data(rows=1000, seed=100)
    X_test_dirty = df_test_dirty[['credit_score', 'income', 'age', 'debt_ratio']].copy()
    y_test = df_test_dirty['approved']
    
    # Evaluate Pipeline A: Feed dirty data directly to model (using median filling to prevent crashes for missing values)
    # (Because raw models crash on NaN, standard pipelines fill NaNs blindly without checking for drift/outliers)
    X_test_pipeline_a = X_test_dirty.copy()
    X_test_pipeline_a['income'] = X_test_pipeline_a['income'].fillna(df_train['income'].median()) # blind fill
    
    y_pred_pipeline_a = model.predict(X_test_pipeline_a)
    pipeline_a_metrics = {
        'accuracy': accuracy_score(y_test, y_pred_pipeline_a),
        'precision': precision_score(y_test, y_pred_pipeline_a),
        'recall': recall_score(y_test, y_pred_pipeline_a),
        'f1': f1_score(y_test, y_pred_pipeline_a)
    }
    print(f"   [Pipeline A Accuracy (Blind Ingest)]: {pipeline_a_metrics['accuracy']:.4f}")
    
    # Step C: Pipeline B (PyDataQuality Validation Gate Active)
    print("Executing Pipeline B (PyDataQuality Gate)...")
    
    # Initialize analyzers for drift checking
    train_analyzer = pdq.analyze_dataframe(df_train, name="Train_Baseline")
    test_analyzer = pdq.analyze_dataframe(df_test_dirty, name="Test_Production")
    
    # 1. Detect Drift
    drift_df = pdq.compare_drift(train_analyzer, test_analyzer)
    credit_drift = drift_df.loc[drift_df['column'] == 'credit_score', 'drift_status'].values[0]
    credit_psi = drift_df.loc[drift_df['column'] == 'credit_score', 'psi'].values[0]
    print(f"      - Credit score drift status: {credit_drift} (PSI: {credit_psi:.4f})")
    
    # 2. Extract outliers and apply systematic cleaning
    X_test_cleaned = X_test_dirty.copy()
    
    # Impute missing income systematically using training median
    X_test_cleaned['income'] = X_test_cleaned['income'].fillna(df_train['income'].median())
    
    # Identify age outliers using PyDataQuality's get_problematic_rows logic
    # Outlier IQR thresholds derived from train baseline
    age_stats = train_analyzer.column_stats['age'].stats
    q1, q3 = age_stats['q1'], age_stats['q3']
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # Cap outlier ages to train boundaries
    X_test_cleaned['age'] = X_test_cleaned['age'].clip(lower=lower_bound, upper=upper_bound)
    
    # Adjust for detected distribution drift (since credit score dropped by 120 points,
    # an intelligent system or engineer can re-align the shifted distribution, 
    # but even just cleaning outliers and missing values demonstrates recovery)
    y_pred_pipeline_b = model.predict(X_test_cleaned)
    pipeline_b_metrics = {
        'accuracy': accuracy_score(y_test, y_pred_pipeline_b),
        'precision': precision_score(y_test, y_pred_pipeline_b),
        'recall': recall_score(y_test, y_pred_pipeline_b),
        'f1': f1_score(y_test, y_pred_pipeline_b)
    }
    print(f"   [Pipeline B Accuracy (Systematic Clean)]: {pipeline_b_metrics['accuracy']:.4f}")
    
    # Compile and save results honestly
    results = {
        'baseline': baseline_metrics,
        'pipeline_a_dirty': pipeline_a_metrics,
        'pipeline_b_cleaned': pipeline_b_metrics,
        'drift_metrics': drift_df.to_dict(orient='records')
    }
    
    output_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(output_dir, 'ml_case_study_results.json'), 'w') as f:
        json.dump(results, f, indent=2, default=str)
        
    print("ML case study data saved successfully.")

if __name__ == '__main__':
    run_ml_case_study()
