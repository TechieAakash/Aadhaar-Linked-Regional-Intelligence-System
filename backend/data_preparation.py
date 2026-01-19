"""
ALRIS - Module 1: Data Preparation Layer
=========================================
Loads, merges, validates, and cleans UIDAI Aadhaar datasets.
Aggregates data at monthly, age-group, and state/district levels.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class DataPreparationLayer:
    """
    Handles all data ingestion and preprocessing for ALRIS.
    """
    
    def __init__(self, base_path):
        """Initialize with base data directory path."""
        self.base_path = base_path
        self.enrolment_path = os.path.join(base_path, 'api_data_aadhar_enrolment')
        self.demographic_path = os.path.join(base_path, 'api_data_aadhar_demographic')
        self.biometric_path = os.path.join(base_path, 'api_data_aadhar_biometric')
        
        # DataFrames storage
        self.enrolment_df = None
        self.demographic_df = None
        self.biometric_df = None
        
        # Aggregated DataFrames
        self.monthly_agg = None
        self.state_agg = None
        self.age_group_agg = None
        
    def load_folder_csvs(self, folder_path, expected_cols=None):
        """
        Load and merge all CSV files from a folder.
        
        Args:
            folder_path: Path to folder containing CSVs
            expected_cols: Optional list of expected column names for validation
            
        Returns:
            Merged DataFrame
        """
        all_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
        print(f"  Found {len(all_files)} CSV files in {os.path.basename(folder_path)}")
        
        dfs = []
        for file in sorted(all_files):
            file_path = os.path.join(folder_path, file)
            df = pd.read_csv(file_path)
            
            # Validate schema consistency
            if expected_cols and not all(col in df.columns for col in expected_cols):
                print(f"  ⚠️ Schema mismatch in {file}")
            
            dfs.append(df)
            print(f"    Loaded {file}: {len(df):,} rows")
        
        merged_df = pd.concat(dfs, ignore_index=True)
        print(f"  ✅ Total merged: {len(merged_df):,} rows")
        return merged_df
    
    def load_all_datasets(self):
        """Load all three datasets from their respective folders."""
        print("\n" + "="*60)
        print("ALRIS DATA INGESTION")
        print("="*60)
        
        # Load Enrolment Data
        print("\n[LOAD] Loading ENROLMENT data...")
        self.enrolment_df = self.load_folder_csvs(
            self.enrolment_path,
            expected_cols=['date', 'state', 'district', 'pincode', 'age_0_5', 'age_5_17', 'age_18_greater']
        )
        
        # Load Demographic Updates
        print("\n[LOAD] Loading DEMOGRAPHIC UPDATES data...")
        self.demographic_df = self.load_folder_csvs(
            self.demographic_path,
            expected_cols=['date', 'state', 'district', 'pincode', 'demo_age_5_17', 'demo_age_17_']
        )
        
        # Load Biometric Updates
        print("\n[LOAD] Loading BIOMETRIC UPDATES data...")
        self.biometric_df = self.load_folder_csvs(
            self.biometric_path,
            expected_cols=['date', 'state', 'district', 'pincode', 'bio_age_5_17', 'bio_age_17_']
        )
        
        return self

    def load_folder_csvs(self, folder_path, expected_cols=None):
        """
        Load and merge all CSV files from a folder.
        """
        all_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
        print(f"  Found {len(all_files)} CSV files in {os.path.basename(folder_path)}")
        
        dfs = []
        for file in sorted(all_files):
            file_path = os.path.join(folder_path, file)
            df = pd.read_csv(file_path)
            
            # Validate schema consistency
            if expected_cols and not all(col in df.columns for col in expected_cols):
                print(f"  [WARN] Schema mismatch in {file}")
            
            dfs.append(df)
            print(f"    Loaded {file}: {len(df):,} rows")
        
        merged_df = pd.concat(dfs, ignore_index=True)
        print(f"  [OK] Total merged: {len(merged_df):,} rows")
        return merged_df

    def clean_dates(self, df, date_col='date'):
        """Normalize date formats to datetime."""
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], format='%d-%m-%Y', errors='coerce')
        return df
    
    def clean_state_names(self, df, state_col='state'):
        """Standardize state names (handle variations like 'Orissa' vs 'Odisha')."""
        df = df.copy()
        state_mapping = {
            'Orissa': 'Odisha',
            'ODISHA': 'Odisha',
            'Pondicherry': 'Puducherry',
            'Andaman and Nicobar': 'Andaman & Nicobar',
            'Jammu and Kashmir': 'Jammu & Kashmir',
        }
        df[state_col] = df[state_col].str.strip()
        df[state_col] = df[state_col].replace(state_mapping)
        
        # Filter out numeric artifacts (e.g., '1000000') and empty strings
        # Keep only states that are NOT numeric and have a reasonable length
        df = df[~df[state_col].str.match(r'^\d+$', na=False)]
        df = df[df[state_col].str.len() > 1]
        
        return df

    def handle_missing_values(self, df, numeric_cols):
        """Fill missing numeric values with 0 (aggregated counts)."""
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].fillna(0).astype(int)
        return df

    def _print_data_summary(self):
        """Print summary statistics of cleaned data."""
        print("\n" + "-"*60)
        print("DATA SUMMARY")
        print("-"*60)
        
        for name, df in [
            ('Enrolment', self.enrolment_df),
            ('Demographic', self.demographic_df),
            ('Biometric', self.biometric_df)
        ]:
            print(f"\n{name}:")
            print(f"  Rows: {len(df):,}")
            print(f"  Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
            print(f"  States: {df['state'].nunique()}")
            print(f"  Districts: {df['district'].nunique()}")

    def remove_duplicates(self, df):
        """Remove duplicate rows."""
        initial_len = len(df)
        df = df.drop_duplicates()
        removed = initial_len - len(df)
        if removed > 0:
            print(f"  Removed {removed:,} duplicate rows")
        return df

    def clean_all_datasets(self):
        """Apply cleaning to all loaded datasets."""
        print("\n" + "="*60)
        print("DATA CLEANING & VALIDATION")
        print("="*60)
        
        # Clean Enrolment data
        print("\n[CLEAN] Cleaning ENROLMENT data...")
        self.enrolment_df = self.clean_dates(self.enrolment_df)
        self.enrolment_df = self.clean_state_names(self.enrolment_df)
        self.enrolment_df = self.remove_duplicates(self.enrolment_df)
        self.enrolment_df = self.handle_missing_values(
            self.enrolment_df, 
            ['age_0_5', 'age_5_17', 'age_18_greater']
        )
        # Add total enrolment column
        self.enrolment_df['total_enrolment'] = (
            self.enrolment_df['age_0_5'] + 
            self.enrolment_df['age_5_17'] + 
            self.enrolment_df['age_18_greater']
        )
        
        # Clean Demographic data
        print("\n[CLEAN] Cleaning DEMOGRAPHIC data...")
        self.demographic_df = self.clean_dates(self.demographic_df)
        self.demographic_df = self.clean_state_names(self.demographic_df)
        self.demographic_df = self.remove_duplicates(self.demographic_df)
        self.demographic_df = self.handle_missing_values(
            self.demographic_df, 
            ['demo_age_5_17', 'demo_age_17_']
        )
        # Add total demographic updates column
        self.demographic_df['total_demo_updates'] = (
            self.demographic_df['demo_age_5_17'] + 
            self.demographic_df['demo_age_17_']
        )
        
        # Clean Biometric data
        print("\n[CLEAN] Cleaning BIOMETRIC data...")
        self.biometric_df = self.clean_dates(self.biometric_df)
        self.biometric_df = self.clean_state_names(self.biometric_df)
        self.biometric_df = self.remove_duplicates(self.biometric_df)
        self.biometric_df = self.handle_missing_values(
            self.biometric_df, 
            ['bio_age_5_17', 'bio_age_17_']
        )
        # Add total biometric updates column
        self.biometric_df['total_bio_updates'] = (
            self.biometric_df['bio_age_5_17'] + 
            self.biometric_df['bio_age_17_']
        )
        
        self._print_data_summary()
        return self

    def create_monthly_aggregation(self):
        """Aggregate data at monthly level for time-series analysis."""
        print("\n[AGG] Creating MONTHLY aggregations...")
        
        # Enrolment monthly
        self.enrolment_df['month'] = self.enrolment_df['date'].dt.to_period('M')
        enrol_monthly = self.enrolment_df.groupby('month').agg({
            'age_0_5': 'sum',
            'age_5_17': 'sum',
            'age_18_greater': 'sum',
            'total_enrolment': 'sum'
        }).reset_index()
        enrol_monthly['month'] = enrol_monthly['month'].astype(str)
        
        # Demographic monthly
        self.demographic_df['month'] = self.demographic_df['date'].dt.to_period('M')
        demo_monthly = self.demographic_df.groupby('month').agg({
            'demo_age_5_17': 'sum',
            'demo_age_17_': 'sum',
            'total_demo_updates': 'sum'
        }).reset_index()
        demo_monthly['month'] = demo_monthly['month'].astype(str)
        
        # Biometric monthly
        self.biometric_df['month'] = self.biometric_df['date'].dt.to_period('M')
        bio_monthly = self.biometric_df.groupby('month').agg({
            'bio_age_5_17': 'sum',
            'bio_age_17_': 'sum',
            'total_bio_updates': 'sum'
        }).reset_index()
        bio_monthly['month'] = bio_monthly['month'].astype(str)
        
        # Merge all monthly data
        self.monthly_agg = enrol_monthly.merge(
            demo_monthly, on='month', how='outer'
        ).merge(
            bio_monthly, on='month', how='outer'
        ).fillna(0).sort_values('month')
        
        print(f"  [OK] Created monthly aggregation: {len(self.monthly_agg)} months")
        return self

    def create_state_aggregation(self):
        """Aggregate data at state level for regional analysis."""
        print("\n[AGG] Creating STATE-LEVEL aggregations...")
        
        # Enrolment by state
        enrol_state = self.enrolment_df.groupby('state').agg({
            'age_0_5': 'sum',
            'age_5_17': 'sum',
            'age_18_greater': 'sum',
            'total_enrolment': 'sum'
        }).reset_index()
        
        # Demographic by state
        demo_state = self.demographic_df.groupby('state').agg({
            'demo_age_5_17': 'sum',
            'demo_age_17_': 'sum',
            'total_demo_updates': 'sum'
        }).reset_index()
        
        # Biometric by state
        bio_state = self.biometric_df.groupby('state').agg({
            'bio_age_5_17': 'sum',
            'bio_age_17_': 'sum',
            'total_bio_updates': 'sum'
        }).reset_index()
        
        # Merge all state data
        self.state_agg = enrol_state.merge(
            demo_state, on='state', how='outer'
        ).merge(
            bio_state, on='state', how='outer'
        ).fillna(0)
        
        # Calculate total updates per state
        self.state_agg['total_updates'] = (
            self.state_agg['total_demo_updates'] + 
            self.state_agg['total_bio_updates']
        )
        
        # Sort by total activity
        self.state_agg = self.state_agg.sort_values('total_enrolment', ascending=False)
        
        print(f"  [OK] Created state aggregation: {len(self.state_agg)} states/UTs")
        return self

    def create_state_monthly_aggregation(self):
        """Create state-wise monthly aggregation for forecasting."""
        print("\n[AGG] Creating STATE-MONTHLY aggregations...")
        
        enrol_state_monthly = self.enrolment_df.groupby(['state', 'month']).agg({
            'total_enrolment': 'sum',
            'age_0_5': 'sum',
            'age_5_17': 'sum',
            'age_18_greater': 'sum'
        }).reset_index()
        enrol_state_monthly['month'] = enrol_state_monthly['month'].astype(str)
        
        self.state_monthly_agg = enrol_state_monthly
        print(f"  [OK] Created state-monthly aggregation: {len(self.state_monthly_agg)} records")
        return self

    def get_processed_data(self):
        """Return all processed DataFrames."""
        return {
            'enrolment': self.enrolment_df,
            'demographic': self.demographic_df,
            'biometric': self.biometric_df,
            'monthly_agg': self.monthly_agg,
            'state_agg': self.state_agg,
            'state_monthly_agg': self.state_monthly_agg
        }

    def save_aggregations(self, output_path):
        """Save aggregated data to CSV and JSON for frontend."""
        print("\n[SAVE] Saving aggregations...")
        
        # Save CSVs to output directory
        csv_path = os.path.join(output_path, 'output', 'data')
        os.makedirs(csv_path, exist_ok=True)
        
        self.monthly_agg.to_csv(os.path.join(csv_path, 'monthly_aggregation.csv'), index=False)
        self.state_agg.to_csv(os.path.join(csv_path, 'state_aggregation.csv'), index=False)
        self.state_monthly_agg.to_csv(os.path.join(csv_path, 'state_monthly_aggregation.csv'), index=False)
        
        # Save JSON for frontend
        json_path = os.path.join(output_path, 'frontend', 'data')
        os.makedirs(json_path, exist_ok=True)
        
        self.monthly_agg.to_json(os.path.join(json_path, 'monthly_data.json'), orient='records')
        self.state_agg.to_json(os.path.join(json_path, 'state_data.json'), orient='records')
        self.state_monthly_agg.to_json(os.path.join(json_path, 'state_monthly_data.json'), orient='records')
        
        print(f"  [OK] Saved to {csv_path}")
        print(f"  [OK] Saved JSON to {json_path}")
        
        return self

def run_data_preparation(base_path):
    """Run the complete data preparation pipeline."""
    dp = DataPreparationLayer(base_path)
    
    # Execute pipeline
    dp.load_all_datasets()
    dp.clean_all_datasets()
    dp.create_monthly_aggregation()
    dp.create_state_aggregation()
    dp.create_state_monthly_aggregation()
    dp.save_aggregations(base_path)
    
    # STAGE 6: Social Vulnerability
    from backend.social_vulnerability import SocialVulnerabilityEngine
    sve = SocialVulnerabilityEngine(base_path)
    sve.ingest_datasets()
    sve.calculate_vulnerability_features()
    sve.calculate_composite_score()
    sve.calculate_peer_benchmarks() # New comparative engine
    
    print("\n" + "="*60)
    print("DATA PREPARATION COMPLETE")
    print("="*60)
    
    return dp


if __name__ == "__main__":
    # Run standalone
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    run_data_preparation(base_path)
