
import json
import numpy as np

# Existing Data Structure (Skeleton)
data = {
    "age_distribution": {
        "0-5 years": {"count": 3473908, "percentage": 65.16, "description": "Infant/Toddler enrolments"},
        "5-17 years": {"count": 1690885, "percentage": 31.72, "description": "Child/Adolescent enrolments"},
        "18+ years": {"count": 166462, "percentage": 3.12, "description": "Adult enrolments"}
    },
    "update_patterns": {
        "demographic_updates": {"5-17 years": 2684483, "17+ years": 24911653, "youth_share": 9.73},
        "biometric_updates": {"5-17 years": 33456559, "17+ years": 34803792, "youth_share": 49.01},
        "biometric_youth_intensity": 49.01
    },
    "risk_analysis": {
        "high_risk_count": 9,
        "medium_risk_count": 43,
        "low_risk_count": 10,
        "high_risk_regions": [
            {"state": "The Dadra And Nagar Haveli And Daman And Diu", "risk_score": 2, "biometric_update_ratio": 0.0, "adult_update_concentration": 0.0},
            {"state": "Westbengal", "risk_score": 2, "biometric_update_ratio": 0.28, "adult_update_concentration": 0.97}
        ]
    }
}

# --- Generate Synthetic Intensity Curves ---
ages = list(range(0, 81)) # 0 to 80

# 1. Biometric Intensity: Spikes at 5 and 15
bio_curve = []
for age in ages:
    val = 5000  # Base line
    if 4 <= age <= 6: val += 450000  # Mandatory at 5
    if 14 <= age <= 16: val += 600000 # Mandatory at 15
    if range(20, 60): val += 2000 # Occasional
    bio_curve.append(val)

# 2. Demographic Intensity: Peak at 20-35 (Job, Marriage, Relocation)
demo_curve = []
for age in ages:
    val = 15000 # Base
    if 18 <= age <= 35: val += 150000 * np.exp(-0.5 * ((age - 26) / 5)**2) # Gaussian peak at 26
    if 5 <= age <= 10: val += 30000 # School
    demo_curve.append(int(val))

# Convert to Dict for JSON
data['demographic_intensity'] = {str(a): int(v) for a, v in zip(ages, demo_curve)}
data['biometric_intensity'] = {str(a): int(v) for a, v in zip(ages, bio_curve)}

# Save
with open(r'C:\Users\AAKASH\OneDrive\Desktop\UIDAI\frontend\data\lifecycle_insights.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Successfully regenerated lifecycle_insights.json with curve data.")
