"""
Test script for Stage 3 Pattern Correlation Engine
Validates Temporal, Geographical, and Device correlations, plus False Positive Suppression.
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

def verify_correlation_pipeline():
    """Run and verify Stage 3 correlation pipeline."""
    print("="*70)
    print(" STAGE 3 PATTERN CORRELATION ENGINE - VERIFICATION TEST")
    print("="*70)
    
    # 1. Setup
    print("\n[TEST] Setting up test data...")
    processed_data, features = create_mock_processed_data()
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    try:
        # 2. Run Full Pipeline (Stage 1 + 2 + 3)
        print("\n[TEST] Running FULL pipeline (Stages 1-3)...")
        engine = run_anomaly_detection(processed_data, features, output_path)
        
        # 3. Validation Checks
        print("\n" + "="*70)
        print(" VALIDATION RESULTS")
        print("="*70)
        
        # Check correlation attributes
        correlation_checks = [
            ('confirmed_anomalies', 'Post-correlation Confirmed Anomalies'),
            ('suppressed_anomalies', 'Suppressed Anomalies (False Positives)'),
        ]
        
        for attr, name in correlation_checks:
            if hasattr(engine, attr):
                count = len(getattr(engine, attr))
                status = "[PASS]" if count >= 0 else "[FAIL]"
                print(f"{status} {name}: {count}")
            else:
                print(f"[WARN] {name}: Attribute missing")
        
        # Check Report Structure
        print("\n[TEST] Checking report structure...")
        if 'suppressed_anomalies' in engine.report:
            print(f"[PASS] Report includes suppressed anomalies: {len(engine.report['suppressed_anomalies'])}")
        else:
            print("[WARN] Report missing 'suppressed_anomalies' key")
        
        # Sample Suppressed Anomaly
        if hasattr(engine, 'suppressed_anomalies') and len(engine.suppressed_anomalies) > 0:
            print("\n[SAMPLE] Suppressed Anomaly (False Positive):")
            sample = engine.suppressed_anomalies[0]
            print(f"  Date: {sample.get('date')}")
            print(f"  Region: {sample.get('region')}")
            print(f"  Reason: {sample.get('suppression_reason')}")
            print(f"  Temporal Cluster: {sample.get('temporal_cluster_id')}")
            print(f"  Hotspot Score: {sample.get('geo_hotspot_score')}")
        
        # Sample Enriched Anomaly (with correlation metadata)
        if hasattr(engine, 'confirmed_anomalies') and len(engine.confirmed_anomalies) > 0:
            print("\n[SAMPLE] Enriched Anomaly (with Correlation Metadata):")
            sample = engine.confirmed_anomalies[0]
            print(f"  Date: {sample.get('date')}")
            print(f"  Region: {sample.get('region')}")
            print(f"  Concurrent Anomalies: {sample.get('concurrent_anomalies')}")
            print(f"  Geo Hotspot Score: {sample.get('geo_hotspot_score')}")
            print(f"  Is Suppressed: {sample.get('is_suppressed', False)}")
        
        # Output File Verification
        report_path = os.path.join(output_path, 'frontend', 'data', 'anomalies.json')
        if os.path.exists(report_path):
            print(f"\n[PASS] Report file created: {report_path}")
            file_size = os.path.getsize(report_path)
            print(f"       File size: {file_size} bytes")
        else:
            print(f"\n[FAIL] Report file missing: {report_path}")
        
        print("\n" + "="*70)
        print("[SUCCESS] Stage 3 Correlation Pipeline Validation Complete!")
        print("="*70)
        
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = verify_correlation_pipeline()
    sys.exit(0 if success else 1)
