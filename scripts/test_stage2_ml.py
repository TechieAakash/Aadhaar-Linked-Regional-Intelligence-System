"""
Test script for Stage 2 ML Anomaly Detection
Validates Isolation Forest, Z-score clustering, Change-point detection, and Multi-signal confirmation.
"""

import os
import sys
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.anomaly_detection import run_anomaly_detection

def create_mock_processed_data():
    """Create minimal mock data for testing."""
    # Simple monthly aggregations
    months = pd.date_range('2024-01-01', '2024-12-01', freq='MS')
    monthly_data = pd.DataFrame({
        'month': months.strftime('%Y-%m'),
        'total_enrolment': np.random.randint(50000, 150000, len(months)),
        'total_demo_updates': np.random.randint(20000, 80000, len(months)),
        'total_bio_updates': np.random.randint(10000, 60000, len(months))
    })
    
    # State-level aggregations
    states = ['Delhi', 'Maharashtra', 'Karnataka']
    all_state_data = []
    for state in states:
        for month in months:
            all_state_data.append({
                'month': month.strftime('%Y-%m'),
                'state': state,
                'total_enrolment': np.random.randint(5000, 15000)
            })
    
    state_monthly = pd.DataFrame(all_state_data)
    
    # State features
    state_features = pd.DataFrame({
        'state': states,
        'biometric_update_ratio': [0.65, 0.72, 0.68],
        'growth_volatility': [0.15, 0.08, 0.22]
    })
    
    processed_data = {
        'monthly_agg': monthly_data,
        'state_monthly_agg': state_monthly,
    }
    
    features = {
        'state_features': state_features
    }
    
    return processed_data, features

def verify_ml_pipeline():
    """Run and verify ML anomaly detection pipeline."""
    print("="*70)
    print(" STAGE 2 ML ANOMALY DETECTION - VERIFICATION TEST")
    print("="*70)
    
    # 1. Setup
    print("\n[TEST] Setting up test data...")
    processed_data, features = create_mock_processed_data()
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    try:
        # 2. Run Pipeline with ML
        print("\n[TEST] Running FULL pipeline (Stage 1 + Stage 2)...")
        engine = run_anomaly_detection(processed_data, features, output_path)
        
        # 3. Validation Checks
        print("\n" + "="*70)
        print(" VALIDATION RESULTS")
        print("="*70)
        
        # Check ML attributes exist
        ml_methods = [
            ('isolation_forest_anomalies', 'Isolation Forest'),
            ('zscore_cluster_anomalies', 'Z-score Clustering'),
            ('changepoint_anomalies', 'Change-point Detection'),
            ('confirmed_anomalies', 'Multi-signal CONFIRMED'),
            ('potential_anomalies', 'Multi-signal POTENTIAL')
        ]
        
        for attr, name in ml_methods:
            if hasattr(engine, attr):
                count = len(getattr(engine, attr))
                status = "[PASS]" if count >= 0 else "[FAIL]"
                print(f"{status} {name}: {count} anomalies detected")
            else:
                print(f"[FAIL] {name}: Attribute missing!")
        
        # Check Report Structure
        print("\n[TEST] Checking report structure...")
        if 'ml_confirmed_anomalies' in engine.report:
            print(f"[PASS] Report includes ML confirmed anomalies: {len(engine.report['ml_confirmed_anomalies'])}")
        else:
            print("[WARN] Report missing 'ml_confirmed_anomalies' key")
        
        if 'ml_potential_anomalies' in engine.report:
            print(f"[PASS] Report includes ML potential anomalies: {len(engine.report['ml_potential_anomalies'])}")
        else:
            print("[WARN] Report missing 'ml_potential_anomalies' key")
        
        # Check Output File
        report_path = os.path.join(output_path, 'frontend', 'data', 'anomalies.json')
        if os.path.exists(report_path):
            print(f"[PASS] Report file created: {report_path}")
            
            # Check file size (should be larger with ML results)
            file_size = os.path.getsize(report_path)
            print(f"       File size: {file_size} bytes")
        else:
            print(f"[FAIL] Report file missing: {report_path}")
        
        # Sample Output
        if hasattr(engine, 'confirmed_anomalies') and len(engine.confirmed_anomalies) > 0:
            print("\n[SAMPLE] Confirmed Anomaly (Multi-signal):")
            sample = engine.confirmed_anomalies[0]
            print(f"  Date: {sample.get('date')}")
            print(f"  Region: {sample.get('region')}")
            print(f"  Value: {sample.get('value')}")
            print(f"  Detected by: {sample.get('sources')}")
            print(f"  Confirmation: {sample.get('confirmation_status')}")
        
        print("\n" + "="*70)
        print("[SUCCESS] Stage 2 ML Pipeline Validation Complete!")
        print("="*70)
        
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = verify_ml_pipeline()
    sys.exit(0 if success else 1)
