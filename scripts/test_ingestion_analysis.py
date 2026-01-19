
import sys
import os
import pandas as pd
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.anomaly_detection import run_anomaly_detection

def create_mock_processed_data():
    """Create minimal mock data for legacy engine compatibility."""
    dates = pd.date_range(start='2025-01-01', periods=12, freq='M')
    
    # Monthly Agg
    monthly_agg = pd.DataFrame({
        'month': dates.strftime('%Y-%m'),
        'total_enrolment': np.random.randint(1000, 5000, size=12),
        'total_demo_updates': np.random.randint(500, 2000, size=12),
        'total_bio_updates': np.random.randint(200, 1000, size=12)
    })
    
    # State Features
    states = ['State_A', 'State_B', 'State_C']
    state_features = pd.DataFrame({
        'state': states,
        'biometric_update_ratio': [0.1, 0.5, 0.05], # 0.05 might trigger state anomaly
        'growth_volatility': [0.02, 0.1, 0.5]
    })
    
    return {
        'monthly_agg': monthly_agg,
        'state_monthly_agg': None
    }, {
        'state_features': state_features
    }

def verify_pipeline():
    print("Starting Verification Pipeline...")
    
    # 1. Setup Mock Data
    processed_data, features = create_mock_processed_data()
    
    # 2. Run Engine
    # Only need valid output path
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    try:
        engine = run_anomaly_detection(processed_data, features, output_path)
        
        # 3. Validation
        print("\n--- VALIDATION RESULTS ---")
        
        # Check Seasonal Anomalies
        if hasattr(engine, 'seasonal_anomalies'):
            print(f"[PASS] Seasonal Anomalies Detected: {len(engine.seasonal_anomalies)}")
            if engine.seasonal_anomalies:
                print(f"       Sample: {engine.seasonal_anomalies[0]['explanation']}")
        else:
            print("[FAIL] 'seasonal_anomalies' attribute missing.")
            
        # Check Center/FPEWS Anomalies
        if engine.center_anomalies:
             print(f"[PASS] Center Anomalies Detected: {len(engine.center_anomalies)}")
        else:
             print("[WARN] No Center Anomalies found (might be random chance, check logic).")

        # Check Output Files
        report_path = os.path.join(output_path, 'frontend', 'data', 'anomalies.json')
        if os.path.exists(report_path):
            print(f"[PASS] Report file created: {report_path}")
        else:
             print(f"[FAIL] Report file missing: {report_path}")
             
    except Exception as e:
        print(f"[FAIL] Pipeline crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_pipeline()
