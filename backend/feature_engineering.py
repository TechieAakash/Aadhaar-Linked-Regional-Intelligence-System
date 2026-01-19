"""
ALRIS - Module 2: Feature Engineering
======================================
Engineers governance-grade features for UIDAI analytics.
All features are designed for explainability and policy insights.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os


class FeatureEngineer:
    """
    Creates analytical features for ALRIS decision support.
    """
    
    def __init__(self, processed_data):
        """
        Initialize with processed data from DataPreparationLayer.
        
        Args:
            processed_data: Dictionary containing all processed DataFrames
        """
        self.enrolment_df = processed_data['enrolment']
        self.demographic_df = processed_data['demographic']
        self.biometric_df = processed_data['biometric']
        self.monthly_agg = processed_data['monthly_agg']
        self.state_agg = processed_data['state_agg']
        self.state_monthly_agg = processed_data['state_monthly_agg']
        
        # Feature DataFrames
        self.state_features = None
        self.monthly_features = None
        self.age_group_features = None
        
    def calculate_update_ratios(self):
        """
        Calculate update ratios for each state.
        
        Features created:
        - biometric_update_ratio: Bio updates / (Bio + Demo updates)
        - update_to_enrolment_ratio: Total updates / Total enrolments
        """
        print("\n[FE] Calculating UPDATE RATIOS...")
        
        self.state_features = self.state_agg.copy()
        
        # Biometric update ratio
        total_updates = (
            self.state_features['total_bio_updates'] + 
            self.state_features['total_demo_updates']
        )
        self.state_features['biometric_update_ratio'] = np.where(
            total_updates > 0,
            self.state_features['total_bio_updates'] / total_updates,
            0
        )
        
        # Update to enrolment ratio
        self.state_features['update_to_enrolment_ratio'] = np.where(
            self.state_features['total_enrolment'] > 0,
            self.state_features['total_updates'] / self.state_features['total_enrolment'],
            0
        )
        
        print("  [OK] Created: biometric_update_ratio, update_to_enrolment_ratio")
        return self
    
    def calculate_age_group_intensity(self):
        """
        Calculate update intensity by age group.
        
        Features created:
        - child_enrolment_share: Share of 0-5 and 5-17 in total enrolment
        - adult_update_concentration: Adult updates as share of total
        """
        print("\n[FE] Calculating AGE GROUP INTENSITY...")
        
        # Child enrolment share
        total_enrol = self.state_features['total_enrolment']
        self.state_features['child_enrolment_share'] = np.where(
            total_enrol > 0,
            (self.state_features['age_0_5'] + self.state_features['age_5_17']) / total_enrol,
            0
        )
        
        # Adult update concentration (17+ age group)
        total_updates = self.state_features['total_updates']
        adult_updates = (
            self.state_features['demo_age_17_'] + 
            self.state_features['bio_age_17_']
        )
        self.state_features['adult_update_concentration'] = np.where(
            total_updates > 0,
            adult_updates / total_updates,
            0
        )
        
        print("  [OK] Created: child_enrolment_share, adult_update_concentration")
        return self
    
    def calculate_regional_growth_rate(self):
        """
        Calculate month-over-month growth rates for states.
        
        Features created:
        - avg_monthly_growth_rate: Average MoM growth in enrolments
        - growth_volatility: Standard deviation of growth rates
        """
        print("\n[FE] Calculating REGIONAL GROWTH RATES...")
        
        state_monthly = self.state_monthly_agg.copy()
        state_monthly = state_monthly.sort_values(['state', 'month'])
        
        # Calculate MoM growth per state
        state_monthly['prev_enrolment'] = state_monthly.groupby('state')['total_enrolment'].shift(1)
        state_monthly['growth_rate'] = np.where(
            state_monthly['prev_enrolment'] > 0,
            (state_monthly['total_enrolment'] - state_monthly['prev_enrolment']) / state_monthly['prev_enrolment'],
            0
        )
        
        # Aggregate growth metrics per state
        growth_stats = state_monthly.groupby('state').agg({
            'growth_rate': ['mean', 'std']
        }).reset_index()
        growth_stats.columns = ['state', 'avg_monthly_growth_rate', 'growth_volatility']
        growth_stats['growth_volatility'] = growth_stats['growth_volatility'].fillna(0)
        
        # Merge with state features
        self.state_features = self.state_features.merge(growth_stats, on='state', how='left')
        self.state_features['avg_monthly_growth_rate'] = self.state_features['avg_monthly_growth_rate'].fillna(0)
        self.state_features['growth_volatility'] = self.state_features['growth_volatility'].fillna(0)
        
        print("  [OK] Created: avg_monthly_growth_rate, growth_volatility")
        return self
    
    def calculate_seasonal_index(self):
        """
        Calculate seasonal patterns in Aadhaar activities.
        
        Features created:
        - peak_month: Month with highest activity
        - seasonal_index: Ratio of peak month to average
        """
        print("\n[FE] Calculating SEASONAL INDEX...")
        
        monthly = self.monthly_agg.copy()
        monthly['total_activity'] = (
            monthly['total_enrolment'] + 
            monthly['total_demo_updates'] + 
            monthly['total_bio_updates']
        )
        
        # Extract month number for seasonality
        monthly['month_num'] = pd.to_datetime(monthly['month']).dt.month
        
        # Calculate average activity per calendar month
        seasonal_pattern = monthly.groupby('month_num').agg({
            'total_activity': 'mean'
        }).reset_index()
        seasonal_pattern.columns = ['month_num', 'avg_activity']
        
        # Find peak month
        peak_month_num = seasonal_pattern.loc[
            seasonal_pattern['avg_activity'].idxmax(), 
            'month_num'
        ]
        avg_activity = seasonal_pattern['avg_activity'].mean()
        peak_activity = seasonal_pattern['avg_activity'].max()
        
        # Seasonal index (peak / average)
        seasonal_index = peak_activity / avg_activity if avg_activity > 0 else 1
        
        # Store as monthly features
        self.monthly_features = monthly.copy()
        self.monthly_features['seasonal_index'] = seasonal_index
        self.monthly_features['peak_month'] = peak_month_num
        
        # Month name mapping
        month_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        
        print(f"  [OK] Peak month: {month_names.get(peak_month_num, 'N/A')}")
        print(f"  [OK] Seasonal index: {seasonal_index:.2f}")
        
        # Store seasonality data
        self.seasonality_data = seasonal_pattern
        self.seasonality_data['month_name'] = self.seasonality_data['month_num'].map(month_names)
        
        return self
    
    def create_age_group_analysis(self):
        """
        Create detailed age-group level features.
        
        Features created:
        - age_group_enrolment_distribution
        - age_group_update_distribution
        """
        print("\n[FE] Creating AGE GROUP ANALYSIS...")
        
        # Aggregate nationally by age groups
        national_enrolment = {
            '0-5 years': self.state_features['age_0_5'].sum(),
            '5-17 years': self.state_features['age_5_17'].sum(),
            '18+ years': self.state_features['age_18_greater'].sum()
        }
        
        national_updates = {
            '5-17 years (Demo)': self.state_features['demo_age_5_17'].sum(),
            '17+ years (Demo)': self.state_features['demo_age_17_'].sum(),
            '5-17 years (Bio)': self.state_features['bio_age_5_17'].sum(),
            '17+ years (Bio)': self.state_features['bio_age_17_'].sum()
        }
        
        self.age_group_features = {
            'enrolment_distribution': national_enrolment,
            'update_distribution': national_updates
        }
        
        # Calculate percentages
        total_enrol = sum(national_enrolment.values())
        for age, val in national_enrolment.items():
            pct = (val / total_enrol * 100) if total_enrol > 0 else 0
            print(f"  {age}: {val:,.0f} ({pct:.1f}%)")
        
        return self
    
    def calculate_service_load_index(self):
        """
        Calculate service load index per state.
        
        Features created:
        - service_load_index: Normalized activity volume
        - load_category: High/Medium/Low service demand
        """
        print("\n[FE] Calculating SERVICE LOAD INDEX...")
        
        # Total activity volume
        self.state_features['total_activity'] = (
            self.state_features['total_enrolment'] + 
            self.state_features['total_updates']
        )
        
        # Normalize to 0-100 scale
        max_activity = self.state_features['total_activity'].max()
        self.state_features['service_load_index'] = np.where(
            max_activity > 0,
            (self.state_features['total_activity'] / max_activity) * 100,
            0
        )
        
        # Categorize load
        def categorize_load(idx):
            if idx >= 50:
                return 'High'
            elif idx >= 20:
                return 'Medium'
            else:
                return 'Low'
        
        self.state_features['load_category'] = self.state_features['service_load_index'].apply(categorize_load)
        
        # Count by category
        for cat in ['High', 'Medium', 'Low']:
            count = (self.state_features['load_category'] == cat).sum()
            print(f"  {cat} Load States: {count}")
        
        return self
    
    def get_features(self):
        """Return all engineered features."""
        return {
            'state_features': self.state_features,
            'monthly_features': self.monthly_features,
            'age_group_features': self.age_group_features,
            'seasonality_data': self.seasonality_data
        }
    
    def save_features(self, output_path):
        """Save engineered features to files."""
        print("\n[SAVE] Saving engineered features...")
        
        # Save to JSON for frontend
        json_path = os.path.join(output_path, 'frontend', 'data')
        os.makedirs(json_path, exist_ok=True)
        
        self.state_features.to_json(
            os.path.join(json_path, 'state_features.json'), 
            orient='records'
        )
        self.monthly_features.to_json(
            os.path.join(json_path, 'monthly_features.json'), 
            orient='records'
        )
        self.seasonality_data.to_json(
            os.path.join(json_path, 'seasonality_data.json'),
            orient='records'
        )
        
        # Age group features
        age_df = pd.DataFrame({
            'category': list(self.age_group_features['enrolment_distribution'].keys()),
            'enrolment': list(self.age_group_features['enrolment_distribution'].values())
        })
        age_df.to_json(os.path.join(json_path, 'age_group_data.json'), orient='records')
        
        # Save to CSV for analysis
        csv_path = os.path.join(output_path, 'output', 'data')
        self.state_features.to_csv(os.path.join(csv_path, 'state_features.csv'), index=False)
        
        print(f"  [OK] Saved features to {json_path}")
        return self


def run_feature_engineering(processed_data, output_path):
    """Run the complete feature engineering pipeline."""
    print("\n" + "="*60)
    print("FEATURE ENGINEERING")
    print("="*60)
    
    fe = FeatureEngineer(processed_data)
    
    fe.calculate_update_ratios()
    fe.calculate_age_group_intensity()
    fe.calculate_regional_growth_rate()
    fe.calculate_seasonal_index()
    fe.create_age_group_analysis()
    fe.calculate_service_load_index()
    fe.save_features(output_path)
    
    print("\n" + "="*60)
    print("[OK] FEATURE ENGINEERING COMPLETE")
    print("="*60)
    
    return fe
