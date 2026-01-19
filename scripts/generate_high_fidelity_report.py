import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# Set High-Resolution Plotting Defaults - Ultra High Quality
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Inter', 'Arial', 'Liberation Sans', 'DejaVu Sans']
sns.set_theme(style="white", context="talk")

# Government/UIDAI Color Palette - Sophisticated & Clean
COLORS = {
    'nic_blue': '#003d62',
    'gov_saffron': '#ff9933',
    'gov_green': '#138808',
    'alert_red': '#dc3545',
    'navy': '#1a365d',
    'slate': '#4a5568',
    'light_gray': '#f8f9fa'
}

OUTPUT_DIR = os.path.join(os.getcwd(), 'static', 'assets', 'infographics')
DATA_DIR = os.path.join(os.getcwd(), 'data')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Regional Zone Mapping for Cleaner Faceted Views
ZONES = {
    'North': ['Jammu & Kashmir', 'Himachal Pradesh', 'Punjab', 'Uttarakhand', 'Haryana', 'Delhi', 'Rajasthan', 'Chandigarh', 'Ladakh'],
    'East': ['Bihar', 'West Bengal', 'Odisha', 'Jharkhand'],
    'West': ['Gujarat', 'Maharashtra', 'Goa', 'Dadra and Nagar Haveli and Daman and Diu'],
    'South': ['Andhra Pradesh', 'Karnataka', 'Kerala', 'Tamil Nadu', 'Telangana', 'Lakshadweep', 'Puducherry', 'Andaman & Nicobar Islands'],
    'Central': ['Madhya Pradesh', 'Chhattisgarh', 'Uttar Pradesh'],
    'North-East': ['Arunachal Pradesh', 'Assam', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Sikkim', 'Tripura']
}

def get_zone(state):
    for zone, states in ZONES.items():
        if state in states:
            return zone
    return 'Other'

def generate_faceted_zonal_bars(df):
    """8K Quality: Faceted Bar Chart by Zone (Reduces Clutter)"""
    print("[HF] Generating Faceted Zonal Bar Graphs...")
    df['zone'] = df['state'].apply(get_zone)
    
    # Sort zones for consistent display
    zones = ['North', 'South', 'East', 'West', 'Central', 'North-East']
    
    fig, axes = plt.subplots(3, 2, figsize=(26, 20), sharey=True)
    axes = axes.flatten()
    
    for i, zone in enumerate(zones):
        zone_df = df[df['zone'] == zone].sort_values('integrated_risk_score', ascending=False)
        sns.barplot(
            data=zone_df, x='state', y='integrated_risk_score', 
            ax=axes[i], palette='Blues_d', hue='state', legend=False
        )
        axes[i].set_title(f"{zone} Zone - Regional Risk Status", fontsize=18, fontweight='bold', color=COLORS['nic_blue'])
        axes[i].tick_params(axis='x', rotation=35)
        axes[i].set_xlabel("")
        axes[i].set_ylabel("Risk Score" if i % 2 == 0 else "")
        
        # Grid for readability
        axes[i].yaxis.grid(True, linestyle='--', alpha=0.3)
        sns.despine(ax=axes[i], left=True)

    plt.suptitle("National Risk Portfolio: Zonal Administrative Breakdown", fontsize=32, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'high_res_faceted_zonal_risk.png'), bbox_inches='tight')
    plt.close()

def generate_temporal_heatmap(df_monthly):
    """8K Quality: Time-Series Heatmap (Month vs State)"""
    print("[HF] Generating Temporal Trend Heatmap...")
    # Get top 15 most active/risky states for clarity
    top_15_states = df_monthly.groupby('state')['total_enrolment'].sum().nlargest(15).index
    df_top = df_monthly[df_monthly['state'].isin(top_15_states)]
    
    pivot_df = df_top.pivot(index='state', columns='month', values='total_enrolment')
    
    plt.figure(figsize=(22, 12))
    sns.heatmap(pivot_df, annot=True, fmt=".0f", cmap='YlGnBu', linewidths=0.5, 
                cbar_kws={'label': 'Monthly Enrolment Volume'})
    
    plt.title("Operational Temporal Heatmap: Monthly Enrolment Intensity (Top 15 Regions)", 
              fontsize=28, fontweight='bold', pad=30)
    plt.xlabel("Month (Fiscal Cycle)", fontsize=18, fontweight='bold')
    plt.ylabel("Administrative Region", fontsize=18, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'high_res_temporal_intensity_heatmap.png'), bbox_inches='tight')
    plt.close()

def generate_advanced_joint_dist(df_risk):
    """8K Quality: Joint Distribution with Marginal Density (Non-Cluttered Scatter)"""
    print("[HF] Generating Advanced Joint Distribution Plot...")
    
    g = sns.JointGrid(data=df_risk, x='social_vulnerability_index', y='integrated_risk_score', height=14)
    
    # Scatter plot in the center
    g.plot_joint(sns.scatterplot, s=150, alpha=0.6, hue=df_risk['service_risk_category'], 
                 palette='rocket', edgecolor='white', linewidth=1.5)
    
    # Histograms/Density on the margins
    g.plot_marginals(sns.histplot, kde=True, color=COLORS['nic_blue'], alpha=0.3)
    
    g.set_axis_labels("Social Vulnerability Index (SVI)", "Integrated Risk Score", 
                      fontsize=18, fontweight='bold')
    
    plt.suptitle("Advanced Risk Correlation with Marginal Density Distributions", 
                 fontsize=28, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'high_res_advanced_joint_correlation.png'), bbox_inches='tight')
    plt.close()

def generate_hierarchical_pie(df_risk):
    """8K Quality: Nested Donut Chart (Zone -> Risk Level)"""
    print("[HF] Generating Hierarchical Risk Donut Chart...")
    df_risk['zone'] = df_risk['state'].apply(get_zone)
    
    zone_data = df_risk.groupby('zone')['integrated_risk_score'].sum()
    cat_data = df_risk.groupby(['zone', 'service_risk_category'])['integrated_risk_score'].count().reset_index()
    
    fig, ax = plt.subplots(figsize=(16, 16))
    size = 0.3
    
    # Outer ring: Zones
    ax.pie(zone_data.values, radius=1, labels=zone_data.index,
           colors=sns.color_palette("muted", len(zone_data)),
           wedgeprops=dict(width=size, edgecolor='w'), pctdistance=0.85,
           textprops={'fontsize': 14, 'fontweight': 'bold'})
    
    # Inner ring: Risk Categories
    group_counts = df_risk.groupby(['zone', 'service_risk_category']).size()
    ax.pie(group_counts.values, radius=1-size, 
           colors=sns.color_palette("pastel", len(group_counts)),
           wedgeprops=dict(width=size, edgecolor='w'))
    
    plt.title("Zonal Risk Composition: Hierarchical Resource Allocation View", 
              fontsize=28, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'high_res_hierarchical_risk_pie.png'), bbox_inches='tight')
    plt.close()

def main():
    risk_path = os.path.join(DATA_DIR, 'integrated_service_risk.csv')
    monthly_path = os.path.join(DATA_DIR, 'state_monthly_aggregation.csv')
    
    if not os.path.exists(risk_path) or not os.path.exists(monthly_path):
        print(f"[ERROR] Data paths not found")
        return

    df_risk = pd.read_csv(risk_path).drop_duplicates(subset=['state'], keep='first')
    df_monthly = pd.read_csv(monthly_path)
    
    print(f"[HF] Starting Advanced Layout Report Generation (8K Optimized)...")
    
    # 1. Zonal Faceted Dashboard
    generate_faceted_zonal_bars(df_risk)
    
    # 2. Temporal Intensity Matrix
    generate_temporal_heatmap(df_monthly)
    
    # 3. Probabilistic Joint Correlation
    generate_advanced_joint_dist(df_risk)
    
    # 4. Multi-level Composition Donut
    generate_hierarchical_pie(df_risk)
    
    print(f"[HF] SUCCESS: Advanced non-cluttered reports generated in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
