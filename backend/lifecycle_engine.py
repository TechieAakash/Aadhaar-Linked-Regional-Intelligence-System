import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import json

# Set style for government-appropriate visualizations
plt.style.use('ggplot')
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['font.family'] = 'sans-serif'


# Government color palette
GOV_COLORS = {
    'primary': '#1a365d',      # Deep blue
    'secondary': '#2c5282',    # Medium blue
    'accent': '#ed8936',       # Saffron
    'success': '#38a169',      # Green
    'warning': '#dd6b20',      # Orange
    'danger': '#e53e3e',       # Red
    'light': '#f7fafc',        # Light gray
    'dark': '#1a202c'          # Dark gray
}


class LifecycleEngine:
    """
    Analyzes lifecycle patterns in Aadhaar data.
    """
    
    def __init__(self, processed_data, features):
        """
        Initialize with processed data and engineered features.
        """
        self.enrolment_df = processed_data['enrolment']
        self.demographic_df = processed_data['demographic']
        self.biometric_df = processed_data['biometric']
        self.state_features = features['state_features']
        self.monthly_features = features['monthly_features']
        
        # Analysis results
        self.lifecycle_insights = {}
        self.risk_groups = []
        
    def analyze_age_distribution(self):
        """
        Analyze enrolment distribution across age groups.
        """
        print("\n[LC] Analyzing AGE DISTRIBUTION...")
        
        # National totals
        total_0_5 = self.state_features['age_0_5'].sum()
        total_5_17 = self.state_features['age_5_17'].sum()
        total_18_plus = self.state_features['age_18_greater'].sum()
        total = total_0_5 + total_5_17 + total_18_plus
        
        age_distribution = {
            '0-5 years': {
                'count': int(total_0_5),
                'percentage': round(total_0_5 / total * 100, 2) if total > 0 else 0,
                'description': 'Infant/Toddler enrolments'
            },
            '5-17 years': {
                'count': int(total_5_17),
                'percentage': round(total_5_17 / total * 100, 2) if total > 0 else 0,
                'description': 'Child/Adolescent enrolments'
            },
            '18+ years': {
                'count': int(total_18_plus),
                'percentage': round(total_18_plus / total * 100, 2) if total > 0 else 0,
                'description': 'Adult enrolments'
            }
        }
        
        self.lifecycle_insights['age_distribution'] = age_distribution
        
        for age, data in age_distribution.items():
            print(f"  {age}: {data['count']:,} ({data['percentage']}%)")
        
        return self
    
    def analyze_update_patterns(self):
        """
        Analyze update patterns by age and type.
        """
        print("\n[LC] Analyzing UPDATE PATTERNS by age...")
        
        # Aggregate update data
        demo_5_17 = self.state_features['demo_age_5_17'].sum()
        demo_17_plus = self.state_features['demo_age_17_'].sum()
        bio_5_17 = self.state_features['bio_age_5_17'].sum()
        bio_17_plus = self.state_features['bio_age_17_'].sum()
        
        update_patterns = {
            'demographic_updates': {
                '5-17 years': int(demo_5_17),
                '17+ years': int(demo_17_plus),
                'youth_share': round(demo_5_17 / (demo_5_17 + demo_17_plus) * 100, 2) if (demo_5_17 + demo_17_plus) > 0 else 0
            },
            'biometric_updates': {
                '5-17 years': int(bio_5_17),
                '17+ years': int(bio_17_plus),
                'youth_share': round(bio_5_17 / (bio_5_17 + bio_17_plus) * 100, 2) if (bio_5_17 + bio_17_plus) > 0 else 0
            }
        }
        
        # Biometric update intensity (mandatory for children 5-15)
        bio_intensity_youth = bio_5_17 / (bio_5_17 + bio_17_plus) * 100 if (bio_5_17 + bio_17_plus) > 0 else 0
        update_patterns['biometric_youth_intensity'] = round(bio_intensity_youth, 2)
        
        self.lifecycle_insights['update_patterns'] = update_patterns
        
        print(f"  Demographic Updates - Youth (5-17): {demo_5_17:,}")
        print(f"  Demographic Updates - Adult (17+): {demo_17_plus:,}")
        print(f"  Biometric Updates - Youth (5-17): {bio_5_17:,}")
        print(f"  Biometric Updates - Adult (17+): {bio_17_plus:,}")
        
        return self
    
    def identify_high_risk_regions(self):
        """
        Identify regions with potential lifecycle compliance issues.
        """
        print("\n[LC] Identifying HIGH-RISK REGIONS...")
        
        # Risk indicators:
        # 1. Low biometric update ratio (< 0.3)
        # 2. High adult update concentration (> 0.9) - suggests youth underserved
        # 3. High growth volatility (> 0.5) - suggests infrastructure issues
        
        risk_df = self.state_features.copy()
        
        # Calculate risk score
        risk_df['low_bio_flag'] = risk_df['biometric_update_ratio'] < 0.3
        risk_df['youth_underserved_flag'] = risk_df['adult_update_concentration'] > 0.9
        risk_df['volatility_flag'] = risk_df['growth_volatility'] > 0.5
        
        risk_df['risk_score'] = (
            risk_df['low_bio_flag'].astype(int) +
            risk_df['youth_underserved_flag'].astype(int) +
            risk_df['volatility_flag'].astype(int)
        )
        
        # Categorize risk
        def categorize_risk(score):
            if score >= 2:
                return 'High'
            elif score == 1:
                return 'Medium'
            else:
                return 'Low'
        
        risk_df['risk_category'] = risk_df['risk_score'].apply(categorize_risk)
        
        # Get high-risk regions
        high_risk = risk_df[risk_df['risk_category'] == 'High'][
            ['state', 'risk_score', 'biometric_update_ratio', 'adult_update_concentration']
        ].to_dict('records')
        
        self.risk_groups = high_risk
        self.lifecycle_insights['risk_analysis'] = {
            'high_risk_count': len(high_risk),
            'medium_risk_count': (risk_df['risk_category'] == 'Medium').sum(),
            'low_risk_count': (risk_df['risk_category'] == 'Low').sum(),
            'high_risk_regions': high_risk
        }
        
        print(f"  High Risk: {len(high_risk)} states")
        print(f"  Medium Risk: {(risk_df['risk_category'] == 'Medium').sum()} states")
        print(f"  Low Risk: {(risk_df['risk_category'] == 'Low').sum()} states")
        
        if high_risk:
            print("\n  [WARN] High-Risk States:")
            for region in high_risk[:5]:
                print(f"    - {region['state']}")
        
        self.risk_df = risk_df
        return self
    
    def generate_lifecycle_curve(self, output_path):
        """
        Generate lifecycle curve visualization.
        """
        print("\n[LC] Generating LIFECYCLE CURVE...")
        
        # Prepare data for visualization
        age_groups = ['0-5 years', '5-17 years', '18+ years']
        
        enrolments = [
            self.state_features['age_0_5'].sum(),
            self.state_features['age_5_17'].sum(),
            self.state_features['age_18_greater'].sum()
        ]
        
        # Calculate derived update values for each age category
        # Note: Updates are for 5-17 and 17+ in data
        updates = [
            0,  # No updates for 0-5
            self.state_features['demo_age_5_17'].sum() + self.state_features['bio_age_5_17'].sum(),
            self.state_features['demo_age_17_'].sum() + self.state_features['bio_age_17_'].sum()
        ]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = np.arange(len(age_groups))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, enrolments, width, label='Enrolments', 
                       color=GOV_COLORS['primary'], alpha=0.8)
        bars2 = ax.bar(x + width/2, updates, width, label='Updates',
                       color=GOV_COLORS['accent'], alpha=0.8)
        
        ax.set_xlabel('Age Group', fontsize=12)
        ax.set_ylabel('Count', fontsize=12)
        ax.set_title('Aadhaar Lifecycle: Enrolments vs Updates by Age Group', 
                    fontsize=14, fontweight='bold', color=GOV_COLORS['dark'])
        ax.set_xticks(x)
        ax.set_xticklabels(age_groups)
        ax.legend()
        
        # Add value labels
        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f'{height:,.0f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=9)
        
        for bar in bars2:
            height = bar.get_height()
            ax.annotate(f'{height:,.0f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        
        # Save
        chart_path = os.path.join(output_path, 'output', 'charts')
        os.makedirs(chart_path, exist_ok=True)
        plt.savefig(os.path.join(chart_path, 'lifecycle_curve.png'), dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  [OK] Saved to {chart_path}/lifecycle_curve.png")
        return self
    
    def generate_state_heatmap(self, output_path):
        """
        Generate heatmap of state-wise activity patterns using matplotlib.
        """
        print("\n[LC] Generating STATE HEATMAP...")
        
        # Prepare data - top 15 states by activity
        top_states = self.state_features.nlargest(15, 'total_activity')
        
        # Create matrix for heatmap
        heatmap_data = top_states[['state', 'age_0_5', 'age_5_17', 'age_18_greater']].set_index('state')
        heatmap_data.columns = ['0-5 years', '5-17 years', '18+ years']
        
        # Normalize for better visualization
        heatmap_normalized = heatmap_data.div(heatmap_data.sum(axis=1), axis=0) * 100
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Use matplotlib imshow instead of seaborn heatmap
        im = ax.imshow(heatmap_normalized.values, cmap='Blues', aspect='auto')
        
        # Set ticks
        ax.set_xticks(np.arange(len(heatmap_normalized.columns)))
        ax.set_yticks(np.arange(len(heatmap_normalized.index)))
        ax.set_xticklabels(heatmap_normalized.columns)
        ax.set_yticklabels(heatmap_normalized.index)
        
        # Add text annotations
        for i in range(len(heatmap_normalized.index)):
            for j in range(len(heatmap_normalized.columns)):
                text = ax.text(j, i, f'{heatmap_normalized.values[i, j]:.1f}',
                              ha='center', va='center', color='black', fontsize=9)
        
        # Add colorbar
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.set_label('Percentage')
        
        ax.set_title('Age Distribution Heatmap - Top 15 States by Activity', 
                    fontsize=14, fontweight='bold', color=GOV_COLORS['dark'])
        ax.set_xlabel('Age Group', fontsize=12)
        ax.set_ylabel('State', fontsize=12)
        
        plt.tight_layout()
        
        chart_path = os.path.join(output_path, 'output', 'charts')
        plt.savefig(os.path.join(chart_path, 'state_heatmap.png'), dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  [OK] Saved to {chart_path}/state_heatmap.png")
        return self
    
    def generate_update_type_analysis(self, output_path):
        """
        Generate visualization comparing update types.
        """
        print("\n[LC] Generating UPDATE TYPE ANALYSIS...")
        
        # Data
        categories = ['5-17 years', '17+ years']
        demo_values = [
            self.state_features['demo_age_5_17'].sum(),
            self.state_features['demo_age_17_'].sum()
        ]
        bio_values = [
            self.state_features['bio_age_5_17'].sum(),
            self.state_features['bio_age_17_'].sum()
        ]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Pie chart for demographic updates
        ax1.pie(demo_values, labels=categories, autopct='%1.1f%%',
               colors=[GOV_COLORS['secondary'], GOV_COLORS['primary']], startangle=90)
        ax1.set_title('Demographic Updates\nby Age Group', fontsize=12, fontweight='bold')
        
        # Pie chart for biometric updates
        ax2.pie(bio_values, labels=categories, autopct='%1.1f%%',
               colors=[GOV_COLORS['accent'], GOV_COLORS['warning']], startangle=90)
        ax2.set_title('Biometric Updates\nby Age Group', fontsize=12, fontweight='bold')
        
        plt.suptitle('Update Type Distribution Analysis', fontsize=14, fontweight='bold',
                    color=GOV_COLORS['dark'], y=1.02)
        plt.tight_layout()
        
        chart_path = os.path.join(output_path, 'output', 'charts')
        plt.savefig(os.path.join(chart_path, 'update_type_analysis.png'), dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  [OK] Saved to {chart_path}/update_type_analysis.png")
        return self
    
    def get_insights(self):
        """Return all lifecycle insights."""
        return self.lifecycle_insights
    
    def save_insights(self, output_path):
        """Save lifecycle insights to JSON."""
        print("\n[SAVE] Saving lifecycle insights...")
        
        from utils import save_json, convert_to_native_types
        
        json_path = os.path.join(output_path, 'frontend', 'data')
        os.makedirs(json_path, exist_ok=True)
        
        # Convert numpy types before saving
        insights_clean = convert_to_native_types(self.lifecycle_insights)
        save_json(insights_clean, os.path.join(json_path, 'lifecycle_insights.json'))
        
        # Save risk analysis separately
        risk_data = self.risk_df[['state', 'risk_category', 'risk_score', 
                                   'biometric_update_ratio', 'adult_update_concentration']].to_dict('records')
        risk_data_clean = convert_to_native_types(risk_data)
        save_json(risk_data_clean, os.path.join(json_path, 'risk_analysis.json'))
        
        print(f"  [OK] Saved to {json_path}")
        return self


def run_lifecycle_analysis(processed_data, features, output_path):
    """Run the complete lifecycle analysis pipeline."""
    print("\n" + "="*60)
    print("LIFECYCLE INTELLIGENCE ENGINE")
    print("="*60)
    
    engine = LifecycleEngine(processed_data, features)
    
    engine.analyze_age_distribution()
    engine.analyze_update_patterns()
    engine.identify_high_risk_regions()
    engine.generate_lifecycle_curve(output_path)
    engine.generate_state_heatmap(output_path)
    engine.generate_update_type_analysis(output_path)
    engine.save_insights(output_path)
    
    print("\n" + "="*60)
    print("[OK] LIFECYCLE ANALYSIS COMPLETE")
    print("="*60)
    
    return engine
