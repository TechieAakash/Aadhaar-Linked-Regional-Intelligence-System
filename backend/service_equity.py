"""
ALRIS - Module 7: Service Equity Index (SEI)
============================================
Quantifies fairness and inclusiveness of Aadhaar services across regions.
Calculates a 0-100 score based on 5 key dimensions.
"""

import pandas as pd
import numpy as np
import os

class ServiceEquityAnalyzer:
    """
    Calculates the Service Equity Index (SEI) using available data proxies.
    """
    
    def __init__(self, processed_data, features):
        """
        Initialize with data from previous pipeline stages.
        """
        self.state_agg = processed_data['state_agg'].copy()
        self.features = features['state_features'].copy()
        
        # Merge features if not already present
        if 'biometric_update_ratio' not in self.state_agg.columns:
            cols_to_merge = [c for c in self.features.columns if c not in self.state_agg.columns and c != 'state']
            if cols_to_merge:
                self.state_agg = self.state_agg.merge(
                    self.features[['state'] + cols_to_merge], 
                    on='state', 
                    how='left'
                )
        
        self.equity_df = None
        self.national_score = 0
        
    def _normalize(self, series):
        """Min-Max normalization to 0-1 scale."""
        min_val = series.min()
        max_val = series.max()
        if max_val == min_val:
            return pd.Series(0.5, index=series.index)
        return (series - min_val) / (max_val - min_val)

    def calculate_metrics(self):
        """
        Calculate the 5 sub-components of SEI.
        """
        df = self.state_agg.copy()
        
        # 1. Service Availability (Proxy: Total Enrolment Volume)
        # Higher enrolment volume implies better infrastructure reach
        df['raw_availability'] = df['total_enrolment']
        
        # 2. Service Utilization (Existing Feature: Update to Enrolment Ratio)
        # Measures how much people use the system for updates relative to base size
        df['raw_utilization'] = df['update_to_enrolment_ratio']
        
        # 3. Service Timeliness (Proxy: Biometric Update absolute volume)
        # High biometric updates (age 5, 15) imply timely mandatory updates
        df['raw_timeliness'] = df['total_bio_updates']
        
        # 4. Regional Load Balance (Proxy: Inverse of Growth Volatility)
        # Less volatile growth = more predictable/balanced load
        # We invert volatility: Higher score = More stable (better)
        # Handle 0 volatility by adding small epsilon or capping
        max_vol = df['growth_volatility'].max() if 'growth_volatility' in df.columns else 1
        df['raw_load_balance'] = 1 - (df['growth_volatility'] / max_vol) if 'growth_volatility' in df.columns else 0.5
        
        # 5. Demographic Coverage (Proxy: Balance between Child and Adult activity)
        # We want to reward states that serve BOTH children (enrolment) and adults (updates)
        # Score = Harmonic mean of Child Share and Adult Share
        df['raw_demo_coverage'] = 2 * (df['child_enrolment_share'] * df['adult_update_concentration']) / \
                                  (df['child_enrolment_share'] + df['adult_update_concentration'] + 1e-9)
        
        # Normalize all metrics to 0-100 scale for display
        df['score_availability'] = self._normalize(df['raw_availability']) * 100
        df['score_utilization'] = self._normalize(df['raw_utilization']) * 100
        df['score_timeliness'] = self._normalize(df['raw_timeliness']) * 100
        df['score_load_balance'] = self._normalize(df['raw_load_balance']) * 100
        df['score_demo_coverage'] = self._normalize(df['raw_demo_coverage']) * 100
        
        self.equity_df = df
        return self

    def calculate_sei_score(self):
        """
        Calculate weighted SEI Score.
        Formula:
        0.25 * Availability +
        0.25 * Utilization +
        0.20 * Timeliness +
        0.15 * Load Balance +
        0.15 * Demo Coverage
        """
        weights = {
            'availability': 0.25,
            'utilization': 0.25,
            'timeliness': 0.20,
            'load_balance': 0.15,
            'demo_coverage': 0.15
        }
        
        self.equity_df['sei_score'] = (
            self.equity_df['score_availability'] * weights['availability'] +
            self.equity_df['score_utilization'] * weights['utilization'] +
            self.equity_df['score_timeliness'] * weights['timeliness'] +
            self.equity_df['score_load_balance'] * weights['load_balance'] +
            self.equity_df['score_demo_coverage'] * weights['demo_coverage']
        )
        
        # Round to 1 decimal
        self.equity_df['sei_score'] = self.equity_df['sei_score'].round(1)
        
        # Calculate National Average
        self.national_score = self.equity_df['sei_score'].mean()
        
        return self
    
    def interpret_scores(self):
        """Add text interpretation based on score ranges."""
        def get_interpretation(score):
            if score >= 80: return "Equitable & Inclusive"
            if score >= 60: return "Moderate Gaps"
            if score >= 40: return "Service Imbalance"
            return "High Exclusion Risk"
            
        self.equity_df['interpretation'] = self.equity_df['sei_score'].apply(get_interpretation)
        
        # Government-style detailed analysis
        def get_gov_analysis(row):
            diff = row['sei_score'] - self.national_score
            status = "above" if diff >= 0 else "below"
            return (f"The Service Equity Index for {row['state']} is {row['sei_score']}, "
                    f"indicating {status}-average access relative to national benchmarks ({self.national_score:.1f}).")
            
        self.equity_df['gov_analysis'] = self.equity_df.apply(get_gov_analysis, axis=1)
        return self

    def get_results(self):
        """Return structured results."""
        # Top 5 and Bottom 5 lists
        sorted_df = self.equity_df.sort_values('sei_score', ascending=False)
        top_perf = sorted_df.head(5)[['state', 'sei_score', 'interpretation']].to_dict('records')
        bottom_perf = sorted_df.tail(5)[['state', 'sei_score', 'interpretation']].to_dict('records')
        
        return {
            'metadata': {
                'index_name': 'Service Equity Index (SEI)',
                'national_average': round(self.national_score, 1),
                'weights': {
                    'availability': '25%',
                    'utilization': '25%',
                    'timeliness': '20%',
                    'load_balance': '15%',
                    'demographic_coverage': '15%'
                }
            },
            'state_scores': self.equity_df.to_dict('records'),
            'insights': {
                'top_performing_states': top_perf,
                'needs_improvement_states': bottom_perf
            }
        }
        
    def save_results(self, output_path):
        """Save results to JSON for frontend."""
        print("\n[SAVE] Saving Equity Index results...")
        
        json_path = os.path.join(output_path, 'frontend', 'data')
        os.makedirs(json_path, exist_ok=True)
        
        # Save full dataset
        self.equity_df.to_json(
            os.path.join(json_path, 'equity_data.json'), 
            orient='records'
        )
        
        # Save summary
        import json
        with open(os.path.join(json_path, 'equity_summary.json'), 'w') as f:
            json.dump(self.get_results(), f, indent=2)
            
        print(f"  [OK] Saved to {json_path}")


def run_service_equity(processed_data, features, output_path):
    """Run the SEI calculation pipeline."""
    print("\n" + "="*60)
    print("SERVICE EQUITY INDEX (SEI) CALCULATION")
    print("="*60)
    
    analyzer = ServiceEquityAnalyzer(processed_data, features)
    analyzer.calculate_metrics()
    analyzer.calculate_sei_score()
    analyzer.interpret_scores()
    analyzer.save_results(output_path)
    
    results = analyzer.get_results()
    print(f"\n[INFO] National Average SEI: {results['metadata']['national_average']}")
    print("\n[TOP] Top Performing States:")
    for state in results['insights']['top_performing_states']:
        print(f"  - {state['state']}: {state['sei_score']} ({state['interpretation']})")
        
    print("\n" + "="*60)
    print("SEI CALCULATION COMPLETE")
    print("="*60)
    
    return results
