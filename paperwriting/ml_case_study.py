import time
import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score
from sklearn.datasets import fetch_california_housing

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
    df['credit_score'] = df['credit_score'] - 120
    df['credit_score'] = np.clip(df['credit_score'], 300, 850)
    
    return df

def run_synthetic_case_study():
    print("--- Synthetic MLOps Validation Case Study ---")
    df_train = generate_base_data(rows=5000, seed=42)
    X = df_train[['credit_score', 'income', 'age', 'debt_ratio']]
    y = df_train['approved']
    
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    y_val_pred = model.predict(X_val)
    baseline_metrics = {
        'accuracy': accuracy_score(y_val, y_val_pred),
        'precision': precision_score(y_val, y_val_pred),
        'recall': recall_score(y_val, y_val_pred),
        'f1': f1_score(y_val, y_val_pred)
    }
    
    df_test_dirty = generate_corrupted_test_data(rows=1000, seed=100)
    X_test_dirty = df_test_dirty[['credit_score', 'income', 'age', 'debt_ratio']].copy()
    y_test = df_test_dirty['approved']
    
    # Pipeline A
    X_test_pipeline_a = X_test_dirty.copy()
    X_test_pipeline_a['income'] = X_test_pipeline_a['income'].fillna(df_train['income'].median())
    y_pred_pipeline_a = model.predict(X_test_pipeline_a)
    pipeline_a_metrics = {
        'accuracy': accuracy_score(y_test, y_pred_pipeline_a),
        'precision': precision_score(y_test, y_pred_pipeline_a),
        'recall': recall_score(y_test, y_pred_pipeline_a),
        'f1': f1_score(y_test, y_pred_pipeline_a)
    }
    
    # Pipeline B
    train_analyzer = pdq.analyze_dataframe(df_train, name="Train_Baseline")
    test_analyzer = pdq.analyze_dataframe(df_test_dirty, name="Test_Production")
    drift_df = pdq.compare_drift(train_analyzer, test_analyzer)
    
    X_test_cleaned = X_test_dirty.copy()
    X_test_cleaned['income'] = X_test_cleaned['income'].fillna(df_train['income'].median())
    
    age_stats = train_analyzer.column_stats['age'].stats
    q1, q3 = age_stats['q1'], age_stats['q3']
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    X_test_cleaned['age'] = X_test_cleaned['age'].clip(lower=lower_bound, upper=upper_bound)
    
    y_pred_pipeline_b = model.predict(X_test_cleaned)
    pipeline_b_metrics = {
        'accuracy': accuracy_score(y_test, y_pred_pipeline_b),
        'precision': precision_score(y_test, y_pred_pipeline_b),
        'recall': recall_score(y_test, y_pred_pipeline_b),
        'f1': f1_score(y_test, y_pred_pipeline_b)
    }
    
    return {
        'baseline': baseline_metrics,
        'pipeline_a': pipeline_a_metrics,
        'pipeline_b': pipeline_b_metrics,
        'drift_metrics': drift_df.to_dict(orient='records')
    }

def run_realworld_case_study():
    print("--- Real-World MLOps Validation Case Study (California Housing) ---")
    data = fetch_california_housing(as_frame=True)
    df = data.frame
    # We will use a subset for faster processing
    df = df.sample(n=6000, random_state=42).reset_index(drop=True)
    
    # Split into train and test conceptually
    df_train = df.iloc[:5000].copy()
    df_test = df.iloc[5000:].copy()
    
    X_train = df_train.drop(columns=['MedHouseVal'])
    y_train = df_train['MedHouseVal']
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    y_train_pred = model.predict(X_train)
    baseline_metrics = {
        'r2': r2_score(y_train, y_train_pred),
        'mse': mean_squared_error(y_train, y_train_pred)
    }
    
    # Corrupt test data: introduce drift in MedInc (income) and anomalies in AveRooms
    df_test_dirty = df_test.copy()
    np.random.seed(100)
    # Missing values
    mask_miss = np.random.rand(len(df_test_dirty)) < 0.1
    df_test_dirty.loc[mask_miss, 'HouseAge'] = np.nan
    # Drift
    df_test_dirty['MedInc'] = df_test_dirty['MedInc'] * 1.5 + 2.0  # Wealthy boom
    # Anomalies
    mask_out = np.random.rand(len(df_test_dirty)) < 0.05
    df_test_dirty.loc[mask_out, 'AveRooms'] = np.random.uniform(50, 100, sum(mask_out))
    
    X_test_dirty = df_test_dirty.drop(columns=['MedHouseVal'])
    y_test = df_test_dirty['MedHouseVal']
    
    # Pipeline A
    X_a = X_test_dirty.copy()
    X_a['HouseAge'] = X_a['HouseAge'].fillna(X_train['HouseAge'].median())
    y_pred_a = model.predict(X_a)
    pipeline_a_metrics = {
        'r2': r2_score(y_test, y_pred_a),
        'mse': mean_squared_error(y_test, y_pred_a)
    }
    
    # Pipeline B
    train_analyzer = pdq.analyze_dataframe(df_train, name="Cali_Train")
    test_analyzer = pdq.analyze_dataframe(df_test_dirty, name="Cali_Test")
    drift_df = pdq.compare_drift(train_analyzer, test_analyzer)
    
    X_b = X_test_dirty.copy()
    X_b['HouseAge'] = X_b['HouseAge'].fillna(X_train['HouseAge'].median())
    
    rooms_stats = train_analyzer.column_stats['AveRooms'].stats
    q1, q3 = rooms_stats['q1'], rooms_stats['q3']
    iqr = q3 - q1
    X_b['AveRooms'] = X_b['AveRooms'].clip(lower=q1-1.5*iqr, upper=q3+1.5*iqr)
    
    y_pred_b = model.predict(X_b)
    pipeline_b_metrics = {
        'r2': r2_score(y_test, y_pred_b),
        'mse': mean_squared_error(y_test, y_pred_b)
    }
    
    return {
        'baseline': baseline_metrics,
        'pipeline_a': pipeline_a_metrics,
        'pipeline_b': pipeline_b_metrics,
        'drift_metrics': drift_df.to_dict(orient='records')
    }

def run_ml_case_study():
    synthetic_res = run_synthetic_case_study()
    realworld_res = run_realworld_case_study()
    
    results = {
        'synthetic': synthetic_res,
        'real_world': realworld_res
    }
    
    output_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(output_dir, 'ml_case_study_results.json'), 'w') as f:
        json.dump(results, f, indent=2, default=str)
        
    print("ML case study data saved successfully.")

if __name__ == '__main__':
    run_ml_case_study()
