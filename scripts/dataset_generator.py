import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_datasets(output_dir):
    """Generates mock datasets for Data Ingestion Layer."""
    print(f"Generating datasets in {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Region-wise Aadhaar Update Volumes (Daily)
    print("- Generating region_update_volumes.csv...")
    dates = pd.date_range(end=datetime.now(), periods=365) # Last 1 year
    regions = ['North', 'South', 'East', 'West', 'Central', 'North-East']
    
    records = []
    for date in dates:
        for region in regions:
            # Base volume with some seasonality
            base_vol = np.random.randint(5000, 15000)
            
            # Weekend dip
            if date.weekday() >= 5:
                base_vol *= 0.6
                
            # Random fluctuation
            vol = int(base_vol * np.random.uniform(0.9, 1.1))
            
            records.append({
                'date': date.strftime('%Y-%m-%d'),
                'region': region,
                'update_volume_count': vol,
                'successful_updates': int(vol * np.random.uniform(0.92, 0.98)),
                'rejected_updates': int(vol * np.random.uniform(0.01, 0.05))
            })
    
    pd.DataFrame(records).to_csv(os.path.join(output_dir, 'region_update_volumes.csv'), index=False)
    
    # 2. Center-level Operational Performance Logs
    print("- Generating center_performance.csv...")
    center_ids = [f'Center_{i:04d}' for i in range(1, 51)] # 50 centers
    
    center_records = []
    for cid in center_ids:
        region = np.random.choice(regions)
        # Generate last 30 days of logs per center
        for day in range(30):
            date = (datetime.now() - timedelta(days=day)).strftime('%Y-%m-%d')
            
            # Normal operating params
            avg_time = np.random.normal(12, 2) # Minutes
            error_rate = np.random.exponential(1.5) # Percent
            
            # Inject anomalies for testing
            if np.random.random() < 0.02: # 2% chance of anomaly
                avg_time = np.random.uniform(1, 3) # Bot-like speed
            if np.random.random() < 0.02:
                error_rate = np.random.uniform(15, 25) # High failure
                
            center_records.append({
                'date': date,
                'center_id': cid,
                'region': region,
                'avg_processing_time_min': round(avg_time, 2),
                'biometric_error_rate_pct': round(error_rate, 2),
                'device_id': f'DEV-{cid}-{np.random.randint(100,999)}',
                'uptime_hours': round(np.random.uniform(6, 12), 1)
            })
            
    pd.DataFrame(center_records).to_csv(os.path.join(output_dir, 'center_performance.csv'), index=False)
    
    # 3. Monthly Baseline Metrics (Population Normalized)
    print("- Generating baseline_metrics.csv...")
    baseline_records = []
    for region in regions:
        baseline_records.append({
            'region': region,
            'avg_daily_updates_per_lakh': np.random.randint(50, 150),
            'std_dev_updates': round(np.random.uniform(5, 15), 2),
            'seasonal_factor_winter': 1.1,
            'seasonal_factor_summer': 0.9,
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        })
    pd.DataFrame(baseline_records).to_csv(os.path.join(output_dir, 'baseline_metrics.csv'), index=False)
    
    print("Dataset generation complete.")

if __name__ == "__main__":
    # Output to the project's output/data folder
    # Assuming script is run from project root, or we find the relative path
    # Using absolute path for safety based on USER context
    OUTPUT_PATH = r"c:\Users\AAKASH\OneDrive\Desktop\UIDAI\output\data"
    generate_datasets(OUTPUT_PATH)
