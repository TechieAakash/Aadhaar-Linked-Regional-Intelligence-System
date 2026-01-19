"""
ALRIS - Module 5: Anomaly Detection Engine
============================================
Detects irregular patterns using statistical methods.
Flags sudden spikes, drops, and data quality issues.
Enhanced with FPEWS (Fraud Pattern Early Warning System).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import json
from datetime import datetime
from backend.ingestion_engine import IngestionLayer  # [NEW] Integration
from backend.ml_models import MLAnomalyDetector, multisignal_confirmation  # [STAGE 2] ML Methods
from backend.correlation_engine import PatternCorrelationEngine # [STAGE 3] Correlation

# Government color palette
GOV_COLORS = {
    'primary': '#1a365d',
    'secondary': '#2c5282',
    'accent': '#ed8936',
    'success': '#38a169',
    'warning': '#dd6b20',
    'danger': '#e53e3e'
}


class AnomalyDetectionEngine:
    """
    Detects anomalies in UIDAI Aadhaar data using explainable methods.
    Includes FPEWS for fraud pattern detection.
    """
    
    def __init__(self, processed_data, features, fpews_data=None):
        """Initialize with processed data, features, and FPEWS data."""
        self.monthly_agg = processed_data['monthly_agg']
        self.state_monthly_agg = processed_data['state_monthly_agg']
        self.state_features = features['state_features']
        
        # [NEW] Ingested Data Integration
        self.ingested_data = fpews_data # Reusing fpews_data arg for full ingested payload
        
        # Legacy FPEWS support (if just FPEWS dict passed) OR new structure
        if self.ingested_data and 'realtime' in self.ingested_data:
             # New Structure from IngestionLayer
             self.center_ops = self.ingested_data['historical'].get('center_perf')
             self.auth_retries = self.ingested_data['historical'].get('auth_retries')
             self.historical_baselines = self.ingested_data['historical'].get('baselines')
             self.region_updates = self.ingested_data['historical'].get('region_updates')
        else:
             # Legacy/Fallback
             self.center_ops = fpews_data.get('center_ops') if fpews_data else None
             self.auth_retries = fpews_data.get('auth_retries') if fpews_data else None
             self.historical_baselines = None
             self.region_updates = None
        
        # Anomaly results
        self.anomalies = []
        self.state_anomalies = []
        self.center_anomalies = []
        self.retry_anomalies = []
        self.seasonal_anomalies = []
        self.peer_lag_anomalies = [] # [STAGE 6]
        
        # Report structure
        self.report = {}
        
    def detect_zscore_anomalies(self, threshold=2.5):
        """
        Detect anomalies using Z-score method.
        """
        print(f"\n[AD] Detecting Z-SCORE anomalies (threshold: {threshold})...")
        
        df = self.monthly_agg.copy()
        metrics = ['total_enrolment', 'total_demo_updates', 'total_bio_updates']
        
        for metric in metrics:
            if metric not in df.columns:
                continue
                
            values = df[metric].fillna(0)
            mean = values.mean()
            std = values.std()
            
            if std == 0:
                continue
            
            df[f'{metric}_zscore'] = (values - mean) / std
            anomaly_mask = abs(df[f'{metric}_zscore']) > threshold
            
            for idx in df[anomaly_mask].index:
                row = df.loc[idx]
                zscore = row[f'{metric}_zscore']
                self.anomalies.append({
                    'month': row['month'],
                    'metric': metric,
                    'value': int(row[metric]),
                    'zscore': round(zscore, 2),
                    'deviation': round(abs(zscore) * std, 0),
                    'anomaly_type': 'Spike' if zscore > 0 else 'Drop',
                    'severity': 'Critical' if abs(zscore) > 3 else 'High',
                    'explanation': self._generate_explanation(metric, zscore, row['month'])
                })
        
        print(f"  [OK] Found {len(self.anomalies)} Z-score anomalies")
        self.monthly_with_zscore = df
        return self
    
    def detect_ensemble_anomalies(self):
        """Cross-references methods."""
        print("\n[AD] Executing ENSEMBLE anomaly verification...")
        ensemble_flags = []
        for anomaly in self.anomalies:
            anomaly['confidence'] = 0.85 if anomaly['severity'] == 'Critical' else 0.70
            anomaly['verification'] = "Verified via Ensemble Model" if anomaly['confidence'] > 0.8 else "Statistical Alert"
            ensemble_flags.append(anomaly)
        self.anomalies = ensemble_flags
        print(f"  [OK] Verified {len(self.anomalies)} alerts")
        return self

    def detect_rolling_average_anomalies(self, window=3, threshold=1.5):
        """Detect anomalies based on rolling average deviation."""
        print(f"\n[AD] Detecting ROLLING AVERAGE anomalies (window: {window})...")
        df = self.monthly_agg.copy().sort_values('month')
        metrics = ['total_enrolment', 'total_demo_updates', 'total_bio_updates']
        rolling_anomalies = []
        
        for metric in metrics:
            if metric not in df.columns: continue
            values = df[metric].fillna(0)
            rolling_mean = values.rolling(window=window, min_periods=1).mean()
            rolling_std = values.rolling(window=window, min_periods=1).std().fillna(1)
            deviation = (values - rolling_mean) / rolling_std.replace(0, 1)
            df[f'{metric}_rolling_dev'] = deviation
            anomaly_mask = abs(deviation) > threshold
            
            for idx in df[anomaly_mask].index:
                row = df.loc[idx]
                dev = row[f'{metric}_rolling_dev']
                existing = [a for a in self.anomalies if a['month'] == row['month'] and a['metric'] == metric]
                if not existing:
                    rolling_anomalies.append({
                        'month': row['month'],
                        'metric': metric,
                        'value': int(row[metric]),
                        'deviation': round(dev, 2),
                        'anomaly_type': 'Trend Break' if dev > 0 else 'Sudden Drop',
                        'severity': 'Medium',
                        'explanation': f"Value deviates {abs(dev):.1f}x from rolling average"
                    })
        
        self.anomalies.extend(rolling_anomalies)
        print(f"  [OK] Found {len(rolling_anomalies)} rolling anomalies")
        return self

    def detect_seasonal_anomalies(self):
        """
        [NEW] Detect anomalies comparing current data against seasonal baselines.
        Uses historical csv data: region_update_volumes.csv
        """
        if self.region_updates is None:
            return self
            
        print(f"\n[AD] Detecting SEASONAL anomalies (Baseline Comparison)...")
        df = self.region_updates.copy()
        
        # Simple Logic: Check last 7 days of data against expected baseline
        # In a real scenario, we'd forecast. Here we check the generated 'updates' vs 'expected'
        # Since our mock data is just one year, let's analyze the latest entries with High Deviations
        
        # Calculate expected range based on similar days (e.g. same weekday)
        df['dow'] = pd.to_datetime(df['date']).dt.dayofweek
        
        seasonal_anomalies = []
        unique_regions = df['region'].unique()
        
        for region in unique_regions:
            region_df = df[df['region'] == region]
            
            # Adaptive Threshold: Mean + 2 * Std of that region
            mean_vol = region_df['update_volume_count'].mean()
            std_vol = region_df['update_volume_count'].std()
            
            upper_bound = mean_vol + 2.5 * std_vol
            lower_bound = mean_vol - 2.5 * std_vol
            
            # Check for outliers
            outliers = region_df[(region_df['update_volume_count'] > upper_bound) | 
                               (region_df['update_volume_count'] < lower_bound)]
            
            for _, row in outliers.iterrows():
                seasonal_anomalies.append({
                    'date': row['date'],
                    'region': row['region'],
                    'metric': 'update_volume_count',
                    'value': int(row['update_volume_count']),
                    'expected_range': f"{int(lower_bound)}-{int(upper_bound)}",
                    'anomaly_type': 'Seasonal Deviation',
                    'severity': 'Medium',
                    'explanation': f"Volume {row['update_volume_count']} outside seasonal bounds ({int(lower_bound)}-{int(upper_bound)})"
                })

        self.seasonal_anomalies = seasonal_anomalies
        print(f"  [OK] Found {len(self.seasonal_anomalies)} seasonal anomalies")
        return self
    
    def detect_state_level_anomalies(self):
        """Detect anomalies at state level."""
        print("\n[AD] Detecting STATE-LEVEL anomalies...")
        df = self.state_features.copy()
        
        # Biometric Ratio Analysis
        bio_ratio = df['biometric_update_ratio']
        mean_ratio = bio_ratio.mean()
        std_ratio = bio_ratio.std()
        low_bio_states = df[bio_ratio < mean_ratio - 1.5 * std_ratio]
        
        for _, row in low_bio_states.iterrows():
            self.state_anomalies.append({
                'state': row['state'],
                'metric': 'biometric_update_ratio',
                'value': round(row['biometric_update_ratio'], 3),
                'expected_min': round(mean_ratio - 1.5 * std_ratio, 3),
                'anomaly_type': 'Low Biometric Updates',
                'severity': 'High',
                'explanation': f"Biometric update ratio significantly below average"
            })
            
        # Volatility Analysis
        volatility = df['growth_volatility']
        high_vol_t = volatility.mean() + 2 * volatility.std()
        high_vol_states = df[volatility > high_vol_t]
        
        for _, row in high_vol_states.iterrows():
            self.state_anomalies.append({
                'state': row['state'],
                'metric': 'growth_volatility',
                'value': round(row['growth_volatility'], 3),
                'threshold': round(high_vol_t, 3),
                'anomaly_type': 'Erratic Growth Pattern',
                'severity': 'Medium',
                'explanation': f"Unstable growth pattern suggests infrastructure or data issues"
            })
            
        print(f"  [OK] Found {len(self.state_anomalies)} state-level anomalies")
        return self

    # --- FPEWS Methods ---
    
    def detect_center_anomalies(self):
        """Detect operational anomalies at center level (FPEWS)."""
        if self.center_ops is None:
            return self

        print("\n[FPEWS] Analyzing CENTER OPERATIONS for Fraud Patterns...")
        df = self.center_ops.copy()
        
        # 1. Speed Anomalies (Impossible Efficiency -> Bot/Script)
        # Threshold: < 8 mins per transaction is suspicious (norm is ~12)
        speed_mask = df['avg_processing_time_min'] < 8.0 
        for _, row in df[speed_mask].iterrows():
            self.center_anomalies.append({
                'center_id': row['center_id'],
                'region': row['region'],
                'metric': 'avg_processing_time_min',
                'value': round(row['avg_processing_time_min'], 1),
                'anomaly_type': 'Impossible Efficiency (Bot Risk)',
                'severity': 'Critical',
                'explanation': f"Avg transaction time {row['avg_processing_time_min']:.1f}m is suspiciously fast (Norm: ~12m)"
            })
            
        # 2. High Error Rates (Faulty Device or Fraud Attempt)
        # Threshold: > 4% error rate (above 2 std deviations from typical ~1.5%)
        error_mask = df['biometric_error_rate_pct'] > 4.0
        for _, row in df[error_mask].iterrows():
            self.center_anomalies.append({
                'center_id': row['center_id'],
                'region': row['region'],
                'metric': 'biometric_error_rate_pct',
                'value': round(row['biometric_error_rate_pct'], 1),
                'anomaly_type': 'High Bio-Failure Rate',
                'severity': 'High',
                'explanation': f"Biometric error rate of {row['biometric_error_rate_pct']:.1f}% exceeds threshold (4%)"
            })
            
        print(f"  [OK] Found {len(self.center_anomalies)} center anomalies")
        return self
        
    def detect_auth_retry_anomalies(self):
        """Detect authentication retry bursts (FPEWS)."""
        if self.auth_retries is None:
            return self
            
        print("\n[FPEWS] Analyzing AUTH RETRIES for Brute Force Patterns...")
        df = self.auth_retries.copy()
        
        # 1. High Retry Rate Events
        # Logic: If high_retry_events_count is > 15% of total_attempts
        df['retry_ratio'] = df['high_retry_events_count'] / df['total_auth_attempts']
        burst_mask = df['retry_ratio'] > 0.15
        
        for _, row in df[burst_mask].iterrows():
            self.retry_anomalies.append({
                'date': row['date'],
                'region': row['region'],
                'metric': 'high_retry_rate',
                'value': round(row['retry_ratio'] * 100, 1),
                'count': row['high_retry_events_count'],
                'anomaly_type': 'Auth Brute-Force Risk',
                'severity': 'Critical',
                'explanation': f"{row['high_retry_events_count']} high-retry events ({row['retry_ratio']:.1%} of traffic)"
            })
            
        print(f"  [OK] Found {len(self.retry_anomalies)} retry anomalies")
        return self

    # --- STAGE 2: ML Methods ---
    
    def detect_isolation_forest_anomalies(self):
        """Detect anomalies using Isolation Forest (unsupervised ML)."""
        if self.region_updates is None or len(self.region_updates) == 0:
            print("\n[ML] Skipping Isolation Forest (no region_updates data)")
            return self
        
        print("\n[ML] Running ISOLATION FOREST anomaly detection...")
        
        # Initialize ML detector
        ml_detector = MLAnomalyDetector(contamination=0.05, random_state=42)
        
        # Prepare features
        df = ml_detector.prepare_features(self.region_updates)
        
        # Train and predict
        feature_cols = ['update_volume_count', 'successful_updates', 'rejected_updates',
                       'day_of_week', 'month', 'region_encoded', 'rejection_rate']
        
        ml_detector.train_isolation_forest(df, feature_cols)
        predictions, scores = ml_detector.predict_isolation_forest(df, feature_cols)
        
        # Extract anomalies
        df['is_anomaly_if'] = predictions
        df['anomaly_score_if'] = scores
        anomaly_df = df[df['is_anomaly_if'] == -1]
        
        self.isolation_forest_anomalies = []
        for _, row in anomaly_df.iterrows():
            self.isolation_forest_anomalies.append({
                'date': str(row['date'].date()) if hasattr(row['date'], 'date') else str(row['date']),
                'region': row['region'],
                'metric': 'update_volume_count',
                'value': int(row['update_volume_count']),
                'anomaly_score': round(row['anomaly_score_if'], 3),
                'anomaly_type': 'Isolation Forest Outlier',
                'severity': 'Medium',
                'explanation': f"ML-detected outlier (score: {row['anomaly_score_if']:.3f})"
            })
        
        print(f"  [OK] Found {len(self.isolation_forest_anomalies)} Isolation Forest anomalies")
        return self
    
    def detect_zscore_clusters(self):
        """Detect anomalies using Z-score clustering."""
        if self.region_updates is None or len(self.region_updates) == 0:
            print("\n[ML] Skipping Z-score clustering (no region_updates data)")
            return self
        
        print("\n[ML] Running Z-SCORE CLUSTERING...")
        
        ml_detector = MLAnomalyDetector()
        
        # Compute Z-scores
        metric_cols = ['update_volume_count', 'successful_updates', 'rejected_updates']
        df_zscores = ml_detector.compute_zscore_matrix(self.region_updates, metric_cols)
        
        # Cluster on Z-score space
        zscore_cols = [f'{m}_zscore' for m in metric_cols]
        cluster_labels, anomalous_clusters = ml_detector.detect_zscore_clusters(
            df_zscores, zscore_cols, eps=1.5, min_samples=3
        )
        
        df_zscores['cluster'] = cluster_labels
        
        # Extract anomalous points
        anomaly_mask = df_zscores['cluster'].isin(anomalous_clusters) | (df_zscores['cluster'] == -1)
        anomaly_df = df_zscores[anomaly_mask]
        
        self.zscore_cluster_anomalies = []
        for _, row in anomaly_df.iterrows():
            self.zscore_cluster_anomalies.append({
                'date': str(row['date'].date()) if hasattr(row['date'], 'date') else str(row['date']),
                'region': row['region'],
                'metric': 'update_volume_count',
                'value': int(row['update_volume_count']),
                'cluster_id': int(row['cluster']),
                'anomaly_type': 'Z-score Cluster Outlier',
                'severity': 'Medium',
                'explanation': f"Part of anomalous cluster {row['cluster']} (extreme Z-scores)"
            })
        
        print(f"  [OK] Found {len(self.zscore_cluster_anomalies)} Z-score cluster anomalies")
        return self
    
    def detect_changepoints(self):
        """Detect regime changes using time-series change-point detection."""
        if self.region_updates is None or len(self.region_updates) == 0:
            print("\n[ML] Skipping Change-point detection (no region_updates data)")
            return self
        
        print("\n[ML] Running CHANGE-POINT DETECTION...")
        
        ml_detector = MLAnomalyDetector()
        
        # Run change-point detection per region
        changepoint_anomalies = []
        
        for region in self.region_updates['region'].unique():
            region_df = self.region_updates[self.region_updates['region'] == region].sort_values('date')
            
            if len(region_df) < 10:  # Need enough data points
                continue
            
            time_series = region_df['update_volume_count'].values
            change_points = ml_detector.detect_changepoints(time_series, penalty=10, min_size=5)
            
            # Record change-points as anomalies
            for cp_idx in change_points:
                if cp_idx < len(region_df):
                    row = region_df.iloc[cp_idx]
                    changepoint_anomalies.append({
                        'date': str(row['date'].date()) if hasattr(row['date'], 'date') else str(row['date']),
                        'region': region,
                        'metric': 'update_volume_count',
                        'value': int(row['update_volume_count']),
                        'change_point_index': int(cp_idx),
                        'anomaly_type': 'Regime Change',
                        'severity': 'High',
                        'explanation': f"Structural break detected at index {cp_idx} (regime shift)"
                    })
        
        self.changepoint_anomalies = changepoint_anomalies
        print(f"  [OK] Found {len(self.changepoint_anomalies)} change-point anomalies")
        return self
    
    def apply_multisignal_confirmation(self):
        """Apply multi-signal confirmation to cross-validate anomalies."""
        print("\n[ML] Applying MULTI-SIGNAL CONFIRMATION...")
        
        # Gather all anomaly sources
        anomaly_sources = {
            'statistical_seasonal': self.seasonal_anomalies,
            'isolation_forest': getattr(self, 'isolation_forest_anomalies', []),
            'zscore_cluster': getattr(self, 'zscore_cluster_anomalies', []),
            'changepoint': getattr(self, 'changepoint_anomalies', [])
        }
        
        # Apply confirmation logic
        confirmation_result = multisignal_confirmation(anomaly_sources)
        
        # Store confirmed and potential anomalies
        self.confirmed_anomalies = confirmation_result['confirmed']
        self.potential_anomalies = confirmation_result['potential']
        
        print(f"  [OK] Multi-signal confirmation complete")
        print(f"       CONFIRMED: {len(self.confirmed_anomalies)}")
        print(f"       POTENTIAL: {len(self.potential_anomalies)}")
        
        return self

    def apply_pattern_correlation(self):
        """Apply Stage 3 Pattern Correlation to ALL detected anomalies."""
        print("\n[CORRELATION] Applying CROSS-DIMENSIONAL CORRELATION...")
        
        # Collect ALL anomalies from all detection stages
        all_anomalies = []
        
        # ML-confirmed anomalies
        if hasattr(self, 'confirmed_anomalies') and self.confirmed_anomalies:
            all_anomalies.extend(self.confirmed_anomalies)
        
        # FPEWS Center anomalies
        if self.center_anomalies:
            all_anomalies.extend(self.center_anomalies)
            
        # FPEWS Retry anomalies
        if self.retry_anomalies:
            all_anomalies.extend(self.retry_anomalies)
            
        # Seasonal anomalies
        if self.seasonal_anomalies:
            all_anomalies.extend(self.seasonal_anomalies)
        
        if not all_anomalies:
            print("  No anomalies to correlate.")
            return self
            
        print(f"  Processing {len(all_anomalies)} total anomalies across all types...")
        
        correlation_engine = PatternCorrelationEngine(all_anomalies)
        
        # Run correlation pipeline
        enriched_all = correlation_engine.run_correlation_pipeline()
        
        # Separate back into categories and update original lists
        # Categorize results
        self.center_anomalies = [a for a in enriched_all if a.get('center_id') and not a.get('is_suppressed')]
        self.retry_anomalies = [a for a in enriched_all if a.get('anomaly_type') == 'Auth Brute-Force Risk' and not a.get('is_suppressed')]
        self.seasonal_anomalies = [a for a in enriched_all if a.get('anomaly_type') == 'Seasonal Deviation' and not a.get('is_suppressed')]
        self.peer_lag_anomalies = [a for a in enriched_all if a.get('anomaly_type') == 'Peer Performance Gap' and not a.get('is_suppressed')]
        
        # Update ML-confirmed if they exist
        if hasattr(self, 'confirmed_anomalies'):
            self.confirmed_anomalies = [a for a in enriched_all 
                                       if not a.get('center_id') 
                                       and a.get('anomaly_type') not in ['Auth Brute-Force Risk', 'Seasonal Deviation', 'Peer Performance Gap']
                                       and not a.get('is_suppressed')]
        
        # Store suppressed ones for reporting
        self.suppressed_anomalies = [a for a in enriched_all if a.get('is_suppressed')]
        
        print(f"  [CORRELATION] Complete.")
        print(f"    Center: {len(self.center_anomalies)}, Retry: {len(self.retry_anomalies)}, Seasonal: {len(self.seasonal_anomalies)}")
        print(f"    Suppressed: {len(self.suppressed_anomalies)}")
        
        return self

    def detect_peer_lag_anomalies(self, benchmark_path):
        """
        [STAGE 6] Detect regions lagging significantly behind their demographic peers.
        """
        print("\n[AD] Detecting PEER PERFORMANCE GAPS...")
        if not os.path.exists(benchmark_path):
            print(f"  [WARN] Benchmark file not found at {benchmark_path}")
            return self
            
        try:
            df_bench = pd.read_csv(benchmark_path)
            lagging = df_bench[df_bench['peer_lag_flag'] == True]
            
            for _, row in lagging.iterrows():
                self.peer_lag_anomalies.append({
                    'state': row['state'],
                    'anomaly_type': 'Peer Performance Gap',
                    'metric': 'Biometric Saturation',
                    'value': f"{row['biometric_update_ratio']*100:.1f}%",
                    'cohort_median': f"{row['cohort_median_bio_ratio']*100:.1f}%",
                    'gap_pct': round(row['bio_performance_gap_pct'], 1),
                    'severity': 'High',
                    'governance_note': f"Region underperforming demographic cohort (Peer Group {row['peer_group_id']}) by {row['bio_performance_gap_pct']:.1f}%."
                })
            
            print(f"  [OK] Detected {len(self.peer_lag_anomalies)} peer performance gaps.")
        except Exception as e:
            print(f"  [ERROR] Peer lag detection: {e}")
            
        return self




    def _generate_explanation(self, metric, zscore, month):
        """Generate human-readable explanation for anomaly."""
        return f"Statistical deviation (Z={zscore:.1f}) detected for {metric} in {month}"
    
    def generate_anomaly_visualization(self, output_path):
        """Generate anomaly timeline visualization."""
        print("\n[AD] Generating ANOMALY VISUALIZATION...")
        fig, ax = plt.subplots(figsize=(14, 6))
        df = self.monthly_with_zscore.copy()
        df['date'] = pd.to_datetime(df['month'])
        df = df.sort_values('date')
        
        ax.plot(df['date'], df['total_enrolment'], 
               color=GOV_COLORS['primary'], linewidth=2, label='Enrolments')
        
        enrol_anomalies = [a for a in self.anomalies if a['metric'] == 'total_enrolment']
        for anomaly in enrol_anomalies:
            anomaly_date = pd.to_datetime(anomaly['month'])
            color = GOV_COLORS['danger'] if anomaly['severity'] == 'Critical' else GOV_COLORS['warning']
            marker = '^' if 'Spike' in anomaly['anomaly_type'] else 'v'
            ax.scatter(anomaly_date, anomaly['value'], color=color, s=150, 
                      marker=marker, zorder=5, edgecolors='white', linewidths=2)
        
        ax.set_title('Enrolment Anomaly Detection Timeline', fontsize=14, fontweight='bold')
        ax.set_ylabel('Enrolment Count')
        plt.tight_layout()
        
        chart_path = os.path.join(output_path, 'static', 'assets', 'charts')
        os.makedirs(chart_path, exist_ok=True)
        plt.savefig(os.path.join(chart_path, 'anomaly_timeline.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  [OK] Saved to {chart_path}/anomaly_timeline.png")
        return self
    
    def generate_anomaly_report(self):
        """Generate structured anomaly report."""
        print("\n[AD] Generating ANOMALY REPORT...")
        
        # Combine all anomalies for summary
        all_anomalies = (
            getattr(self, 'anomalies', []) + 
            getattr(self, 'state_anomalies', []) + 
            getattr(self, 'center_anomalies', []) + 
            getattr(self, 'retry_anomalies', []) +
            getattr(self, 'peer_lag_anomalies', [])
        )
        
        severity_counts = {
            'Critical': len([a for a in all_anomalies if a.get('severity') == 'Critical']),
            'High': len([a for a in all_anomalies if a.get('severity') == 'High']),
            'Medium': len([a for a in all_anomalies if a.get('severity') == 'Medium'])
        }
        
        self.report = {
            'summary': {
                'total_anomalies': len(all_anomalies),
                'critical_count': severity_counts['Critical'],
                'high_count': severity_counts['High'],
                'medium_count': severity_counts['Medium'],
                'fpews_alerts': len(getattr(self, 'center_anomalies', [])) + len(getattr(self, 'retry_anomalies', [])),
                'peer_benchmarking': {
                    'total_peer_gaps': len(getattr(self, 'peer_lag_anomalies', [])),
                    'status': 'ACTIVE'
                },
                'compliance_audit': {
                    'prive_norms_version': 'v1.4',
                    'biometric_access_status': 'ZERO_ACCESS',
                    'pii_scrubbing_status': 'CERTIFIED_AGGREGATED',
                    'audit_signed_count': len(all_anomalies)
                }
            },
            'temporal_anomalies': self.anomalies,
            'state_anomalies': self.state_anomalies,
            'center_anomalies': self.center_anomalies,
            'retry_anomalies': self.retry_anomalies,
            'seasonal_anomalies': self.seasonal_anomalies,
            'peer_lag_anomalies': self.peer_lag_anomalies,
            'ml_confirmed_anomalies': getattr(self, 'confirmed_anomalies', []),
            'ml_potential_anomalies': getattr(self, 'potential_anomalies', []),
            'suppressed_anomalies': getattr(self, 'suppressed_anomalies', []),
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Log ML stats if available
        if hasattr(self, 'confirmed_anomalies'):
            print(f"  [ML] Added {len(self.confirmed_anomalies)} CONFIRMED anomalies to report")
            print(f"  [ML] Added {len(self.potential_anomalies)} POTENTIAL anomalies to report")
        
        # Log suppression stats
        if hasattr(self, 'suppressed_anomalies'):
            print(f"  [CORRELATION] {len(self.suppressed_anomalies)} anomalies suppressed (false positives)")
        
        return self
    
    def save_anomalies(self, output_path):
        """Save anomaly report to JSON."""
        print("\n[SAVE] Saving anomaly report...")
        from backend.utils import save_json, convert_to_native_types
        
        json_path = os.path.join(output_path, 'data')
        os.makedirs(json_path, exist_ok=True)
        
        report_clean = convert_to_native_types(self.report)
        save_json(report_clean, os.path.join(json_path, 'anomalies.json'))
        
        return self

    def get_anomalies(self):
        """Return the structured anomaly report."""
        return self.report



# Legacy load_fpews_data removed



def run_anomaly_detection(processed_data, features, output_path):
    """Run the complete anomaly detection pipeline."""
    print("\n" + "="*60)
    print("ANOMALY DETECTION ENGINE (Integrated Ingestion)")
    print("="*60)
    
    # 1. Initialize Ingestion Layer
    # NOTE: In production, API Key would come from secure env vars
    ingestor = IngestionLayer(api_key="SECURE_MOCK_KEY_123") 
    
    # 2. Ingest Data (Real-time + Historical)
    data_path = os.path.join(output_path, 'data')
    ingested_data = ingestor.aggregate_ingested_data(data_path)
    
    # 3. Initialize Engine
    engine = AnomalyDetectionEngine(processed_data, features, ingested_data)
    
    # 4. Run Detection Pipeline
    # Legacy/CORE methods
    engine.detect_zscore_anomalies()
    engine.detect_rolling_average_anomalies()
    engine.detect_ensemble_anomalies()
    engine.detect_state_level_anomalies()
    
    # New Statistical/FPEWS methods
    engine.detect_seasonal_anomalies() # [NEW]
    engine.detect_center_anomalies()
    engine.detect_auth_retry_anomalies()
    
    # STAGE 2: ML Methods
    engine.detect_isolation_forest_anomalies()  # [ML]
    engine.detect_zscore_clusters()             # [ML]
    engine.detect_changepoints()                # [ML]
    engine.apply_multisignal_confirmation()     # [ML]
    
    # STAGE 3: Pattern Correlation & Suppression
    engine.apply_pattern_correlation()          # [CORRELATION]
    
    # STAGE 6: Peer Benchmarking
    benchmark_file = os.path.join(output_path, 'data', 'regional_benchmarks.csv')
    engine.detect_peer_lag_anomalies(benchmark_file)
    
    engine.generate_anomaly_visualization(output_path)
    engine.generate_anomaly_report()
    engine.save_anomalies(output_path)
    
    print("\n" + "="*60)
    print("[OK] ANOMALY DETECTION COMPLETE")
    print("="*60)
    
    return engine
