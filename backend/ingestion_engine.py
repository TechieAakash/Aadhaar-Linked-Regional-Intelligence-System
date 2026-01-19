
import pandas as pd
import numpy as np
import os
import time
from datetime import datetime, timedelta

class IngestionLayer:
    """
    Handles data ingestion from simulated UIDAI Secure APIs and local CSV datasets.
    Ensures privacy by only processing aggregated metadata.
    """
    
    def __init__(self, api_key):
        """Initialize with secure API key (Mock validation)."""
        if not api_key:
            raise ValueError("API Key is required for secure ingestion.")
        self.api_key = api_key
        print(f"[INGEST] Ingestion Layer initialized with Key: {api_key[:4]}****")
        
    # --- Simulated Secure APIs ---
    
    def fetch_api_enrolment_counts(self, region=None):
        """Simulates fetching real-time enrolment counts (Time-stamped)."""
        print(f"[API] Fetching enrolment counts" + (f" for {region}" if region else " [ALL]"))
        time.sleep(0.5) # Network latency simulation
        
        # Simulate response
        count = np.random.randint(100, 500)
        return {
            'timestamp': datetime.now().isoformat(),
            'type': 'enrolment_count',
            'count': count,
            'status': 'success'
        }

    def fetch_api_bio_update_logs(self):
        """Simulates fetching biometric update logs (Count-only, no bio data)."""
        print("[API] Fetching biometric update logs...")
        time.sleep(0.3)
        return {
            'timestamp': datetime.now().isoformat(),
            'update_events': np.random.randint(50, 200),
            'data_accessed': 'NONE (Metadata Only)',
            'status': 'success'
        }

    def fetch_api_center_metadata(self, center_id):
        """Simulates fetching center metadata."""
        print(f"[API] Fetching metadata for center: {center_id}")
        return {
            'center_id': center_id,
            'location': 'Region-X', # Mock
            'device_id': f'DEV-{center_id}-X',
            'last_sync': datetime.now().isoformat(),
            'status': 'active'
        }
        
    def fetch_api_auth_retries(self):
        """Simulates fetching aggregated auth retry frequency."""
        print("[API] Fetching auth retry aggregations...")
        return {
            'timestamp': datetime.now().isoformat(),
            'total_attempts': np.random.randint(10000, 50000),
            'retry_count_1': np.random.randint(1000, 2000),
            'retry_count_2': np.random.randint(500, 1000),
            'retry_count_3_plus': np.random.randint(100, 300),
            'status': 'success'
        }

    # --- Historical Dataset Loading ---

    def load_historical_datasets(self, data_path):
        """Loads required CSV datasets for baseline analysis."""
        datasets = {}
        files = {
            'region_updates': 'region_update_volumes.csv',
            'center_perf': 'center_performance.csv',
            'baselines': 'baseline_metrics.csv',
            'auth_retries': 'auth_retries.csv'
        }
        
        print(f"[INGEST] Loading historical datasets from {data_path}...")
        
        for key, filename in files.items():
            full_path = os.path.join(data_path, filename)
            if os.path.exists(full_path):
                try:
                    df = pd.read_csv(full_path)
                    datasets[key] = df
                    print(f"  [OK] Loaded {filename} ({len(df)} records)")
                except Exception as e:
                    print(f"  [ERR] Failed to load {filename}: {e}")
            else:
                print(f"  [WARN] File not found: {filename}")
                
        return datasets

    def aggregate_ingested_data(self, data_path):
        """
        Main method to gather all data for the pipeline.
        Combines API snapshots with historical context.
        """
        print("\n[INGEST] Starting aggregated data collection cycle...")
        
        # 1. Fetch live API snapshots (Simulated)
        api_snapshot = {
            'enrolment_latest': self.fetch_api_enrolment_counts(),
            'bio_updates_latest': self.fetch_api_bio_update_logs(),
            'auth_retries_latest': self.fetch_api_auth_retries()
        }
        
        # 2. Load Long-term history
        historical_data = self.load_historical_datasets(data_path)
        
        return {
            'realtime': api_snapshot,
            'historical': historical_data
        }
