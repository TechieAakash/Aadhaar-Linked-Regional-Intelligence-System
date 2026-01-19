import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

DATA_DIR = os.path.join('output', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def generate_center_operations():
    print("Generating Center Operations Data...")
    np.random.seed(42)
    n_centers = 500
    
    data = {
        'center_id': [f'IND-{10000+i}' for i in range(n_centers)],
        'region': np.random.choice(['North', 'South', 'East', 'West', 'Central'], n_centers),
        'operator_id': [f'OP-{np.random.randint(100, 999)}' for _ in range(n_centers)],
        'daily_transactions': np.random.normal(50, 15, n_centers).astype(int),
        'avg_time_per_tx_min': np.random.normal(12, 3, n_centers),
        'biometric_error_rate': np.random.beta(2, 50, n_centers) * 100,  # Skewed low
        'incident_count': np.random.poisson(0.2, n_centers)
    }
    
    df = pd.DataFrame(data)
    
    # Inject Anomalies (Bot-like speed)
    anom_idx = np.random.choice(n_centers, 5, replace=False)
    df.loc[anom_idx, 'avg_time_per_tx_min'] = np.random.uniform(1.5, 3.0, 5) # Impossible speed
    df.loc[anom_idx, 'daily_transactions'] = np.random.randint(150, 250, 5) # High volume
    df.loc[anom_idx, 'incident_count'] = 0 # "Perfect" but fake
    
    # Inject Anomalies (High Errors - Faulty Device or Fraud)
    error_idx = np.random.choice(n_centers, 5, replace=False)
    df.loc[error_idx, 'biometric_error_rate'] = np.random.uniform(25, 45, 5) 
    
    output_path = os.path.join(DATA_DIR, 'center_operations.csv')
    df.to_csv(output_path, index=False)
    print(f" Saved to {output_path}")

def generate_auth_retries():
    print("Generating Auth Retries Data...")
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    records = []
    
    for date in dates:
        # Base traffic
        daily_vol = np.random.randint(5000, 7000)
        # Normal retries
        retries = np.random.poisson(1, daily_vol)
        
        # Inject Attack Vector (Brute Force Spike)
        if np.random.random() > 0.8: # 20% chance of attack day
            attack_vol = np.random.randint(500, 1000)
            attack_retries = np.random.randint(5, 15, attack_vol)
            
            # Add normal
            for _ in range(daily_vol):
                records.append({
                    'timestamp': date, 
                    'auth_type': np.random.choice(['Fingerprint', 'Iris', 'OTP'], p=[0.6, 0.3, 0.1]),
                    'retry_count': np.random.choice([0, 1, 2], p=[0.8, 0.15, 0.05])
                })
            # Add attack
            for r in attack_retries:
                records.append({
                    'timestamp': date,
                    'auth_type': 'Fingerprint', # Focused attack
                    'retry_count': r
                })
        else:
             for _ in range(daily_vol):
                records.append({
                    'timestamp': date, 
                    'auth_type': np.random.choice(['Fingerprint', 'Iris', 'OTP'], p=[0.6, 0.3, 0.1]),
                    'retry_count': np.random.choice([0, 1, 2], p=[0.8, 0.15, 0.05])
                })
                
    # To save space, we aggregate this by day/type/retry_bucket for the CSV usually, 
    # but for detection raw stream simulator is fine if small enough.
    # Let's aggregate to "Hourly" counts per center for the CSV to match "Aggregated Metadata" constraint.
    
    # Mock Aggregated Output
    agg_data = {
        'date': [],
        'region': [],
        'total_auth_attempts': [],
        'high_retry_events_count': [], # >3 retries
        'avg_retry_rate': []
    }
    
    regions = ['North', 'South', 'East', 'West', 'Central']
    for date in dates:
        for reg in regions:
            attempts = np.random.randint(1000, 5000)
            high_retries = int(attempts * np.random.uniform(0.01, 0.05))
            
            # Anomaly spike
            if np.random.random() > 0.95:
                high_retries = int(attempts * 0.25) # 25% high retries!
            
            agg_data['date'].append(date)
            agg_data['region'].append(reg)
            agg_data['total_auth_attempts'].append(attempts)
            agg_data['high_retry_events_count'].append(high_retries)
            agg_data['avg_retry_rate'].append(round(high_retries/attempts, 3))

    df = pd.DataFrame(agg_data)
    output_path = os.path.join(DATA_DIR, 'auth_retries.csv')
    df.to_csv(output_path, index=False)
    print(f" Saved to {output_path}")

if __name__ == "__main__":
    generate_center_operations()
    generate_auth_retries()
