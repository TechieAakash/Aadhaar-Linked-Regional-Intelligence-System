"""
ALRIS - Module 6: Decision Support Framework
==============================================
Translates analytics insights into policy-ready recommendations.
Rule-based governance intelligence for UIDAI decision-makers.
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime


class DecisionSupportFramework:
    """
    Generates explainable, ethical, and data-backed policy recommendations.
    """
    
    def __init__(self, lifecycle_insights, forecasts, anomalies, features):
        """Initialize with all analysis results."""
        self.lifecycle = lifecycle_insights
        self.forecasts = forecasts
        self.anomalies = anomalies
        self.features = features
        
        # Recommendations storage
        self.recommendations = []
        self.alerts = []
        self.action_items = []
        
    def analyze_biometric_compliance(self):
        """
        Rule: IF biometric update rate for youth drops below threshold
        THEN recommend targeted biometric update drives
        """
        print("\n[DS] Analyzing BIOMETRIC COMPLIANCE...")
        
        update_patterns = self.lifecycle.get('update_patterns', {})
        bio_youth_intensity = update_patterns.get('biometric_youth_intensity', 0)
        
        # Threshold: Youth should represent at least 20% of biometric updates
        # (since mandatory updates are required for 5-15 age group)
        if bio_youth_intensity < 20:
            self.recommendations.append({
                'id': 'REC-BIO-001',
                'category': 'Biometric Compliance',
                'priority': 'High',
                'title': 'Youth Biometric Update Campaign Needed',
                'finding': f'Youth (5-17) represent only {bio_youth_intensity:.1f}% of biometric updates',
                'recommendation': 'Launch targeted mobile biometric update drives in schools and community centers',
                'impact': 'Ensures compliance with mandatory biometric update requirements for minors',
                'target_audience': ['District Collectors', 'Education Department', 'UIDAI Regional Offices'],
                'timeline': 'Within 3 months',
                'kpi': 'Increase youth biometric update share to >30%'
            })
            
            self.alerts.append({
                'type': 'warning',
                'message': f'Youth biometric updates are below expected levels ({bio_youth_intensity:.1f}%)',
                'action': 'Review biometric update accessibility for minors'
            })
        
        print(f"  Youth biometric intensity: {bio_youth_intensity:.1f}%")
        return self
    
    def analyze_regional_disparities(self):
        """
        Rule: IF state has high risk score AND low service load index
        THEN recommend infrastructure enhancement
        """
        print("\n[DS] Analyzing REGIONAL DISPARITIES...")
        
        risk_analysis = self.lifecycle.get('risk_analysis', {})
        high_risk_regions = risk_analysis.get('high_risk_regions', [])
        
        state_features = self.features.get('state_features')
        if state_features is None:
            return self
        
        for region in high_risk_regions:
            state = region['state']
            state_data = state_features[state_features['state'] == state]
            
            if len(state_data) > 0:
                load_category = state_data.iloc[0].get('load_category', 'Unknown')
                
                self.recommendations.append({
                    'id': f'REC-REG-{len(self.recommendations)+1:03d}',
                    'category': 'Regional Infrastructure',
                    'priority': 'High' if load_category == 'High' else 'Medium',
                    'title': f'Address Service Gaps in {state}',
                    'finding': f'{state} identified as high-risk with bio ratio {region["biometric_update_ratio"]:.2f}',
                    'recommendation': 'Deploy additional enrolment centers and mobile units',
                    'impact': 'Improved service accessibility and reduced regional disparities',
                    'target_audience': ['UIDAI State Office', 'State IT Department'],
                    'timeline': 'Within 6 months',
                    'kpi': 'Increase biometric update ratio to national average'
                })
        
        if high_risk_regions:
            self.alerts.append({
                'type': 'critical',
                'message': f'{len(high_risk_regions)} states identified as high-risk for service delivery',
                'action': 'Prioritize infrastructure investment in flagged states'
            })
        
        print(f"  High-risk regions: {len(high_risk_regions)}")
        return self
    
    def analyze_demand_forecasts(self):
        """
        Rule: IF forecasted demand exceeds capacity threshold
        THEN recommend capacity planning measures
        """
        print("\n[DS] Analyzing DEMAND FORECASTS...")
        
        stress_periods = self.forecasts.get('forecasts', {}).get('stress_periods', {})
        critical_periods = [p for p in stress_periods.get('periods', []) 
                          if p.get('stress_level') == 'Critical']
        
        if critical_periods:
            months = ', '.join([p['month'] for p in critical_periods[:3]])
            self.recommendations.append({
                'id': 'REC-CAP-001',
                'category': 'Capacity Planning',
                'priority': 'High',
                'title': 'Address Critical Infrastructure Stress Periods',
                'finding': f'Critical stress periods detected: {months}',
                'recommendation': 'Increase temporary staffing and extend operating hours during peak periods',
                'impact': 'Reduced wait times and improved citizen satisfaction',
                'target_audience': ['UIDAI Operations', 'HR Department'],
                'timeline': 'Before next peak period',
                'kpi': 'Maintain average service time under 15 minutes'
            })
        
        # Check ARIMA forecast trend
        arima = self.forecasts.get('forecasts', {}).get('arima', {})
        if arima and 'forecast_values' in arima:
            forecast_avg = np.mean(arima['forecast_values'])
            
            self.action_items.append({
                'title': 'Prepare for Forecasted Demand',
                'description': f'Expected average monthly enrolment: {forecast_avg:,.0f}',
                'owner': 'UIDAI Planning Division',
                'due_date': 'Ongoing'
            })
        
        print(f"  Critical stress periods: {len(critical_periods)}")
        return self
    
    def analyze_anomalies(self):
        """
        Rule: IF critical anomalies detected
        THEN flag for investigation
        """
        print("\n[DS] Analyzing ANOMALIES for action...")
        
        summary = self.anomalies.get('summary', {})
        critical_count = summary.get('critical_count', 0)
        
        if critical_count > 0:
            critical_anomalies = [a for a in self.anomalies.get('temporal_anomalies', [])
                                 if a.get('severity') == 'Critical']
            
            self.recommendations.append({
                'id': 'REC-ANO-001',
                'category': 'Data Quality & Investigation',
                'priority': 'Critical',
                'title': 'Investigate Critical Data Anomalies',
                'finding': f'{critical_count} critical anomalies detected requiring investigation',
                'recommendation': 'Conduct detailed investigation of flagged periods for data quality or operational issues',
                'impact': 'Ensures data integrity and identifies potential fraud or system issues',
                'target_audience': ['UIDAI Data Quality Team', 'Vigilance Division'],
                'timeline': 'Immediate',
                'kpi': 'Resolve all critical anomalies within 30 days'
            })
            
            self.alerts.append({
                'type': 'critical',
                'message': f'{critical_count} critical anomalies require immediate attention',
                'action': 'Review anomaly report and initiate investigation'
            })
        
        # State-level anomalies
        state_anomalies = self.anomalies.get('state_anomalies', [])
        if state_anomalies:
            states = list(set([a['state'] for a in state_anomalies]))
            self.action_items.append({
                'title': 'Review State-Level Anomalies',
                'description': f'{len(states)} states flagged for irregular patterns',
                'owner': 'UIDAI Regional Directors',
                'due_date': 'Within 2 weeks'
            })
        
        print(f"  Critical anomalies: {critical_count}")
        return self
    
    def analyze_lifecycle_gaps(self):
        """
        Rule: IF age group shows underrepresentation
        THEN recommend targeted outreach
        """
        print("\n[DS] Analyzing LIFECYCLE GAPS...")
        
        age_dist = self.lifecycle.get('age_distribution', {})
        
        # Check if 0-5 age group is underrepresented
        child_pct = age_dist.get('0-5 years', {}).get('percentage', 0)
        
        if child_pct < 10:
            self.recommendations.append({
                'id': 'REC-OUT-001',
                'category': 'Outreach & Awareness',
                'priority': 'Medium',
                'title': 'Infant Aadhaar Enrolment Campaign',
                'finding': f'0-5 age group represents only {child_pct:.1f}% of enrolments',
                'recommendation': 'Partner with hospitals and anganwadis for birth-linked Aadhaar enrolment',
                'impact': 'Ensures early Aadhaar coverage for government scheme benefits',
                'target_audience': ['Health Department', 'Women & Child Development'],
                'timeline': 'Ongoing',
                'kpi': 'Achieve 90% coverage of newborns within 6 months of birth'
            })
        
        print(f"  Child (0-5) enrolment percentage: {child_pct:.1f}%")
        return self
    
    def generate_executive_summary(self):
        """
        Generate executive summary for senior officials.
        """
        print("\n[DS] Generating EXECUTIVE SUMMARY...")
        
        # Prioritize recommendations
        priority_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        self.recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'Medium'), 2))
        
        self.executive_summary = {
            'report_title': 'ALRIS Decision Support Report',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overview': {
                'total_recommendations': len(self.recommendations),
                'critical_recommendations': len([r for r in self.recommendations if r['priority'] == 'Critical']),
                'high_priority_recommendations': len([r for r in self.recommendations if r['priority'] == 'High']),
                'active_alerts': len(self.alerts),
                'action_items': len(self.action_items)
            },
            'key_findings': [
                'Lifecycle analysis reveals age-specific patterns in Aadhaar usage',
                'Regional disparities identified in service accessibility',
                'Demand forecasting indicates predictable seasonal patterns',
                'Anomaly detection has flagged periods requiring investigation'
            ],
            'immediate_actions': [r for r in self.recommendations if r['priority'] in ['Critical', 'High']][:5],
            'alerts': self.alerts,
            'action_items': self.action_items
        }
        
        print(f"  Total recommendations: {len(self.recommendations)}")
        print(f"  Critical/High priority: {self.executive_summary['overview']['critical_recommendations'] + self.executive_summary['overview']['high_priority_recommendations']}")
        
        return self
    
    def get_recommendations(self):
        """Return all recommendations."""
        return {
            'executive_summary': self.executive_summary,
            'recommendations': self.recommendations,
            'alerts': self.alerts,
            'action_items': self.action_items
        }
    
    def save_recommendations(self, output_path):
        """Save recommendations to files."""
        print("\n[SAVE] Saving recommendations...")
        
        from utils import save_json, convert_to_native_types
        
        # JSON for frontend
        json_path = os.path.join(output_path, 'frontend', 'data')
        os.makedirs(json_path, exist_ok=True)
        
        output = self.get_recommendations()
        output_clean = convert_to_native_types(output)
        save_json(output_clean, os.path.join(json_path, 'recommendations.json'))
        
        # Executive summary report
        report_path = os.path.join(output_path, 'output', 'reports')
        os.makedirs(report_path, exist_ok=True)
        
        summary_clean = convert_to_native_types(self.executive_summary)
        recs_clean = convert_to_native_types(self.recommendations)
        
        save_json(summary_clean, os.path.join(report_path, 'executive_summary.json'))
        save_json(recs_clean, os.path.join(report_path, 'policy_recommendations.json'))
        
        print(f"  [OK] Saved to {json_path} and {report_path}")
        return self


def run_decision_support(lifecycle_insights, forecasts, anomalies, features, output_path):
    """Run the complete decision support pipeline."""
    print("\n" + "="*60)
    print("DECISION SUPPORT FRAMEWORK")
    print("="*60)
    
    dsf = DecisionSupportFramework(lifecycle_insights, forecasts, anomalies, features)
    
    dsf.analyze_biometric_compliance()
    dsf.analyze_regional_disparities()
    dsf.analyze_demand_forecasts()
    dsf.analyze_anomalies()
    dsf.analyze_lifecycle_gaps()
    print("\n[DS] Generating RECOMMENDATIONS...")
    print(f"  [OK] Generated {len(dsf.recommendations)} policy actions")
    dsf.generate_executive_summary()
    dsf.save_recommendations(output_path)
    
    print("\n" + "="*60)
    print("DECISION SUPPORT SYSTEM")
    print("[OK] DECISION SUPPORT COMPLETE")
    print("="*60)
    
    return dsf
    return dsf
