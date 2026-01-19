"""
ML Models for Anomaly Detection
Provides helper functions for training and applying ML-based anomaly detection models.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import ruptures as rpt


class MLAnomalyDetector:
    """
    Encapsulates ML-based anomaly detection models.
    """
    
    def __init__(self, contamination=0.05, random_state=42):
        """
        Initialize ML detector with configuration.
        
        Args:
            contamination: Expected proportion of outliers (for Isolation Forest)
            random_state: Random seed for reproducibility
        """
        self.contamination = contamination
        self.random_state = random_state
        self.isolation_forest = None
        self.scaler = StandardScaler()
        
    def prepare_features(self, df):
        """
        Engineer features for ML models from raw data.
        
        Args:
            df: DataFrame with columns: date, region, update_volume_count, etc.
            
        Returns:
            DataFrame with engineered features
        """
        features = df.copy()
        
        # Convert date to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(features['date']):
            features['date'] = pd.to_datetime(features['date'])
        
        # Temporal features
        features['day_of_week'] = features['date'].dt.dayofweek
        features['day_of_month'] = features['date'].dt.day
        features['month'] = features['date'].dt.month
        features['week_of_year'] = features['date'].dt.isocalendar().week
        
        # Regional encoding (label encoding for simplicity)
        region_map = {r: i for i, r in enumerate(features['region'].unique())}
        features['region_encoded'] = features['region'].map(region_map)
        
        # Derived metrics
        features['rejection_rate'] = features['rejected_updates'] / (features['update_volume_count'] + 1e-6)
        features['success_rate'] = features['successful_updates'] / (features['update_volume_count'] + 1e-6)
        
        return features
    
    def train_isolation_forest(self, df, feature_cols):
        """
        Train Isolation Forest model on provided features.
        
        Args:
            df: DataFrame with features
            feature_cols: List of column names to use as features
            
        Returns:
            Trained IsolationForest model
        """
        print(f"[ML] Training Isolation Forest with contamination={self.contamination}...")
        
        X = df[feature_cols].values
        
        # Handle any NaN/Inf
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        self.isolation_forest = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100
        )
        
        self.isolation_forest.fit(X)
        print(f"[ML] Isolation Forest trained on {X.shape[0]} samples, {X.shape[1]} features.")
        
        return self.isolation_forest
    
    def predict_isolation_forest(self, df, feature_cols):
        """
        Predict anomalies using trained Isolation Forest.
        
        Args:
            df: DataFrame with features
            feature_cols: List of column names (must match training)
            
        Returns:
            Array of predictions (-1 for anomaly, 1 for normal)
        """
        if self.isolation_forest is None:
            raise ValueError("Isolation Forest not trained. Call train_isolation_forest first.")
        
        X = df[feature_cols].values
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        predictions = self.isolation_forest.predict(X)
        scores = self.isolation_forest.score_samples(X)
        
        return predictions, scores
    
    def compute_zscore_matrix(self, df, metric_cols):
        """
        Compute Z-scores for specified metrics within each region.
        
        Args:
            df: DataFrame with region and metrics
            metric_cols: List of metric column names
            
        Returns:
            DataFrame with Z-score columns added
        """
        print(f"[ML] Computing Z-scores for metrics: {metric_cols}...")
        
        result = df.copy()
        
        for metric in metric_cols:
            # Compute Z-score per region
            result[f'{metric}_zscore'] = result.groupby('region')[metric].transform(
                lambda x: (x - x.mean()) / (x.std() + 1e-6)
            )
        
        return result
    
    def detect_zscore_clusters(self, df, zscore_cols, eps=1.5, min_samples=3):
        """
        Apply DBSCAN clustering on Z-score space and identify anomalous clusters.
        
        Args:
            df: DataFrame with Z-score columns
            zscore_cols: List of Z-score column names to cluster on
            eps: DBSCAN neighborhood radius
            min_samples: Minimum samples for a core point
            
        Returns:
            Array of cluster labels, list of anomalous cluster IDs
        """
        print(f"[ML] Applying DBSCAN clustering (eps={eps}, min_samples={min_samples})...")
        
        X = df[zscore_cols].values
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        cluster_labels = dbscan.fit_predict(X)
        
        # Identify anomalous clusters (with extreme mean Z-scores)
        anomalous_clusters = []
        unique_clusters = set(cluster_labels)
        unique_clusters.discard(-1)  # -1 is noise in DBSCAN
        
        for cluster_id in unique_clusters:
            cluster_mask = cluster_labels == cluster_id
            cluster_zscores = X[cluster_mask]
            
            # Check if cluster has extreme mean
            mean_zscore = np.abs(cluster_zscores.mean(axis=0)).max()
            if mean_zscore > 3.0:  # Threshold for anomalous cluster
                anomalous_clusters.append(cluster_id)
        
        print(f"[ML] Found {len(unique_clusters)} clusters, {len(anomalous_clusters)} anomalous.")
        
        return cluster_labels, anomalous_clusters
    
    def detect_changepoints(self, time_series, penalty=10, min_size=5):
        """
        Detect change-points in a time series using PELT algorithm.
        
        Args:
            time_series: 1D array or Series of values
            penalty: Penalty value for PELT (higher = fewer change-points)
            min_size: Minimum segment size
            
        Returns:
            List of change-point indices
        """
        print(f"[ML] Running PELT change-point detection (penalty={penalty})...")
        
        signal = np.array(time_series)
        signal = np.nan_to_num(signal, nan=0.0, posinf=0.0, neginf=0.0)
        
        # PELT with RBF kernel
        algo = rpt.Pelt(model="rbf", min_size=min_size).fit(signal)
        change_points = algo.predict(pen=penalty)
        
        # Remove the last index (end of series)
        if change_points and change_points[-1] == len(signal):
            change_points = change_points[:-1]
        
        print(f"[ML] Detected {len(change_points)} change-points.")
        
        return change_points


def multisignal_confirmation(anomaly_sources):
    """
    Apply multi-signal confirmation logic to prioritize anomalies.
    
    Args:
        anomaly_sources: Dict mapping source name to list of anomaly records
                        Example: {'statistical': [...], 'isolation_forest': [...], 'changepoint': [...]}
    
    Returns:
        Dict with 'confirmed' and 'potential' anomaly lists
    """
    print("[ML] Applying multi-signal confirmation...")
    
    # Create a dictionary to track detection count per anomaly signature
    # Signature: (date, region, metric) tuple
    detection_counts = {}
    anomaly_details = {}
    
    for source, anomalies in anomaly_sources.items():
        for anomaly in anomalies:
            # Create signature
            sig = (anomaly.get('date'), anomaly.get('region'), anomaly.get('metric', 'general'))
            
            if sig not in detection_counts:
                detection_counts[sig] = set()
                anomaly_details[sig] = anomaly.copy()
                anomaly_details[sig]['detected_by'] = []
            
            detection_counts[sig].add(source)
            anomaly_details[sig]['detected_by'].append(source)
    
    # Classify anomalies
    confirmed = []
    potential = []
    
    for sig, sources in detection_counts.items():
        anomaly = anomaly_details[sig]
        anomaly['detection_count'] = len(sources)
        anomaly['sources'] = ', '.join(sources)
        
        if len(sources) >= 2:
            anomaly['confirmation_status'] = 'CONFIRMED'
            anomaly['severity'] = 'High'  # Upgrade severity for confirmed
            confirmed.append(anomaly)
        else:
            anomaly['confirmation_status'] = 'POTENTIAL'
            potential.append(anomaly)
    
    print(f"[ML] Confirmation complete: {len(confirmed)} CONFIRMED, {len(potential)} POTENTIAL")
    
    return {
        'confirmed': confirmed,
        'potential': potential
    }
