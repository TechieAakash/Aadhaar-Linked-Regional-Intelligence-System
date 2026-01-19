"""
ALRIS - Main Orchestrator
===========================
Aadhaar Lifecycle & Regional Intelligence System

Executes all analytics modules and generates outputs for the dashboard.
"""

import os
import sys
import json
from datetime import datetime

# Import ALRIS modules
from data_preparation import run_data_preparation
from feature_engineering import run_feature_engineering
from lifecycle_engine import run_lifecycle_analysis
from forecasting_engine import run_forecasting
from anomaly_detection import run_anomaly_detection
from decision_support import run_decision_support
from service_equity import run_service_equity


def print_banner():
    """Print ALRIS banner."""
    banner = """
    ===================================================================
                                                                   
         ALRIS - Aadhaar Lifecycle & Regional Intelligence System   
                                                                   
         UIDAI Analytics Platform                                       
                                                                   
    ===================================================================
    """
    print(banner)


def run_alris(base_path=None):
    """
    Execute the complete ALRIS analytics pipeline.
    
    Args:
        base_path: Root directory containing data folders. 
                   Defaults to parent of this script's directory.
    """
    start_time = datetime.now()
    
    print_banner()
    print(f"\n[TIME] Analysis started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Set base path
    if base_path is None:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print(f"[DIR] Working directory: {base_path}")
    
    # =========================================================================
    # MODULE 1: Data Preparation
    # =========================================================================
    dp = run_data_preparation(base_path)
    processed_data = dp.get_processed_data()
    
    # =========================================================================
    # MODULE 2: Feature Engineering
    # =========================================================================
    fe = run_feature_engineering(processed_data, base_path)
    features = fe.get_features()
    
    # Update processed data with features
    processed_data['state_features'] = features['state_features']
    
    # =========================================================================
    # MODULE 3: Lifecycle Intelligence
    # =========================================================================
    lifecycle = run_lifecycle_analysis(processed_data, features, base_path)
    lifecycle_insights = lifecycle.get_insights()
    
    # =========================================================================
    # MODULE 4: Regional Demand Forecasting
    # =========================================================================
    forecast = run_forecasting(processed_data, features, base_path)
    forecast_results = forecast.get_forecasts()
    
    # =========================================================================
    # MODULE 5: Anomaly Detection
    # =========================================================================
    anomaly = run_anomaly_detection(processed_data, features, base_path)
    anomaly_results = anomaly.get_anomalies()
    
    # =========================================================================
    # MODULE 6: Decision Support Framework
    # =========================================================================
    dsf = run_decision_support(
        lifecycle_insights, 
        forecast_results, 
        anomaly_results, 
        features,
        base_path
    )
    recommendations = dsf.get_recommendations()

    # =========================================================================
    # MODULE 7: Service Equity Index
    # =========================================================================
    equity_results = run_service_equity(
        processed_data,
        features,
        base_path
    )
    
    # =========================================================================
    # Generate Final Summary
    # =========================================================================
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    summary = {
        'pipeline': 'ALRIS Analytics Pipeline',
        'version': '1.0.0',
        'execution_time': f'{duration:.2f} seconds',
        'started_at': start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'completed_at': end_time.strftime('%Y-%m-%d %H:%M:%S'),
        'modules_executed': [
            'Data Preparation',
            'Feature Engineering',
            'Lifecycle Intelligence',
            'Demand Forecasting',
            'Anomaly Detection',
            'Decision Support',
            'Service Equity Index'
        ],
        'outputs': {
            'charts': os.path.join(base_path, 'output', 'charts'),
            'reports': os.path.join(base_path, 'output', 'reports'),
            'frontend_data': os.path.join(base_path, 'frontend', 'data')
        },
        'statistics': {
            'total_enrolment_records': len(processed_data.get('enrolment', [])),
            'total_demographic_records': len(processed_data.get('demographic', [])),
            'total_biometric_records': len(processed_data.get('biometric', [])),
            'states_analyzed': processed_data.get('state_agg', pd.DataFrame()).shape[0] if hasattr(processed_data.get('state_agg'), 'shape') else 0,
            'recommendations_generated': len(recommendations.get('recommendations', [])),
            'anomalies_detected': anomaly_results.get('summary', {}).get('total_anomalies', 0)
        }
    }
    
    # Save pipeline summary
    json_path = os.path.join(base_path, 'frontend', 'data')
    with open(os.path.join(json_path, 'pipeline_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print final summary
    print("\n" + "="*70)
    print("ALRIS ANALYTICS PIPELINE COMPLETE")
    print("="*70)
    print(f"""
    Execution time: {duration:.2f} seconds
    Data processed:
        - Enrolment records: {summary['statistics']['total_enrolment_records']:,}
        - Demographic records: {summary['statistics']['total_demographic_records']:,}
        - Biometric records: {summary['statistics']['total_biometric_records']:,}
    
    Analysis results:
        - States analyzed: {summary['statistics']['states_analyzed']}
        - Recommendations: {summary['statistics']['recommendations_generated']}
        - Anomalies detected: {summary['statistics']['anomalies_detected']}
    
    Output locations:
        - Charts: {summary['outputs']['charts']}
        - Reports: {summary['outputs']['reports']}
        - Frontend data: {summary['outputs']['frontend_data']}
    
    Open frontend/index.html in a browser to view the dashboard
    """)
    print("="*70 + "\n")
    
    return {
        'processed_data': processed_data,
        'features': features,
        'lifecycle_insights': lifecycle_insights,
        'forecasts': forecast_results,
        'anomalies': anomaly_results,
        'recommendations': recommendations,
        'equity_index': equity_results,
        'summary': summary
    }


# Import pandas for summary statistics
import pandas as pd


if __name__ == "__main__":
    # Allow custom path from command line
    if len(sys.argv) > 1:
        run_alris(sys.argv[1])
    else:
        run_alris()
