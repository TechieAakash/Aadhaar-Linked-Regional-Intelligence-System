import os
import json
import csv
import base64
import random
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template, Response
from flask_cors import CORS



app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# --- Configuration & Security ---
DEFAULT_KEY = "579b464db66ec23bdd000001623c2de44ffb40755360bbc473134c16"
UIDAI_API_KEY = os.environ.get("UIDAI_API_KEY", DEFAULT_KEY)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

def validate_api_key():
    """Helper to validate API Key from request headers or query params (for downloads)."""
    api_key = request.headers.get('x-api-key') or \
              request.headers.get('X-Api-Key') or \
              request.args.get('key')  # Support for direct browser downloads
    if not api_key or api_key != UIDAI_API_KEY:
        return False
    return True

def unauthorized_response():
    return jsonify({"error": "Unauthorized: Valid UIDAI API Key required"}), 401

# --- Frontend Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<page>')
def serve_page(page):
    # Normalize page name (handle hyphens)
    page_key = page.replace('-', '_')
    
    # Map friendly names to templates
    template_map = {
        'lifecycle': 'lifecycle.html',
        'equity': 'equity_index.html',
        'planning': 'resource_planning.html',
        'social_risk': 'social_risk.html',
        'forecasting': 'forecasting.html',
        'anomalies': 'anomalies.html',
        'benchmarking': 'benchmarking.html',
        'decisions': 'decisions.html',
        'help': 'help.html',
        'feedback': 'feedback.html',
        'terms': 'terms.html',
        'execution_plan': 'execution_plan.html',
        'equity_insights': 'equity_insights.html',
        'policy_simulator': 'policy_simulator.html'
    }
    
    template = template_map.get(page_key) or template_map.get(page)
    if template:
        return render_template(template)
    
    # Try serving from public directory if not a template
    public_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')
    if os.path.exists(os.path.join(public_dir, f"{page}.html")):
        return send_from_directory(public_dir, f"{page}.html")
    if os.path.exists(os.path.join(public_dir, f"{page_key}.html")):
        return send_from_directory(public_dir, f"{page_key}.html")
    
    return "Page not found", 404

@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory('static/assets', path)

@app.route('/css/<path:path>')
def serve_css(path):
    return send_from_directory('static/css', path)

@app.route('/js/<path:path>')
def serve_js(path):
    return send_from_directory('static/js', path)

# --- API Routes (Consolidated from api/*.py) ---

# 1. Data Service Logic
@app.route('/api/data/<filename>')
def get_data(filename):
    if not filename.endswith('.json'):
        return jsonify({"error": "Only JSON files allowed"}), 400
    
    file_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    
    return jsonify({"error": f"File {filename} not found"}), 404

@app.route('/api/train', methods=['POST'])
def train_trigger():
    if not validate_api_key():
        return unauthorized_response()
    
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Lazy load heavy modules to speed up server startup
        from backend.data_preparation import run_data_preparation
        from backend.feature_engineering import run_feature_engineering
        from backend.lifecycle_engine import run_lifecycle_analysis
        from backend.forecasting_engine import run_forecasting
        from backend.anomaly_detection import run_anomaly_detection
        from backend.decision_support import run_decision_support
        from backend.service_equity import run_service_equity

        # MODULE 1: Data Preparation
        dp = run_data_preparation(base_path)
        processed_data = dp.get_processed_data()
        
        # MODULE 2: Feature Engineering
        fe = run_feature_engineering(processed_data, base_path)
        features = fe.get_features()
        processed_data['state_features'] = features['state_features']
        
        # MODULE 3: Lifecycle Intelligence
        lifecycle = run_lifecycle_analysis(processed_data, features, base_path)
        lifecycle_insights = lifecycle.get_insights()
        
        # MODULE 4: Regional Demand Forecasting
        forecast = run_forecasting(processed_data, features, base_path)
        forecast_results = forecast.get_forecasts()
        
        # MODULE 5: Anomaly Detection
        anomaly = run_anomaly_detection(processed_data, features, base_path)
        anomaly_results = anomaly.get_anomalies()
        
        # MODULE 6: Decision Support Framework
        dsf = run_decision_support(
            lifecycle_insights, 
            forecast_results, 
            anomaly_results, 
            features,
            base_path
        )
        recommendations = dsf.get_recommendations()

        # MODULE 7: Service Equity Index
        equity_results = run_service_equity(
            processed_data,
            features,
            base_path
        )
        
        return jsonify({
            "status": "Success", 
            "message": "ALRIS Analytics Pipeline executed successfully.",
            "statistics": {
                "total_enrolment_records": len(processed_data.get('enrolment', [])),
                "anomalies_detected": anomaly_results.get('summary', {}).get('total_anomalies', 0)
            }
        })
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

# 2. Operations & Social Export Logic
@app.route('/api/operations/export/csv')
@app.route('/api/social/export/csv')
def export_csv():
    if not validate_api_key():
        return unauthorized_response()
    
    data_path = os.path.join(DATA_DIR, 'integrated_service_risk.csv')
    if not os.path.exists(data_path):
        return jsonify({"error": "Risk data not found"}), 404
    
    with open(data_path, 'rb') as f:
        content = f.read()
        
    return Response(
        content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=Regional_Analysis_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@app.route('/api/operations/export/pdf')
@app.route('/api/social/export/pdf')
def export_pdf():
    if not validate_api_key():
        return unauthorized_response()
    
    try:
        from fpdf import FPDF
        
        data_path = os.path.join(DATA_DIR, 'integrated_service_risk.csv')
        if not os.path.exists(data_path):
            return jsonify({"error": "Risk data not found"}), 404
            
        data = []
        states_seen = set()
        with open(data_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                state = row.get('state')
                if state and state not in states_seen:
                    data.append(row)
                    states_seen.add(state)
        
        def get_risk(x):
            try: return float(x.get('integrated_risk_score', 0))
            except: return 0.0
        data.sort(key=get_risk, reverse=True)
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 16)
        pdf.cell(0, 10, 'UIDAI - Regional Classification Analysis Report', 0, 1, 'C')
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")}', 0, 1, 'C')
        pdf.ln(5)
        
        # Table Headers
        col_widths = [60, 35, 30, 45, 20]
        headers_text = ['State / UT', 'Vuln. Score', 'Coverage %', 'Risk Category', 'Rank']
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_fill_color(0, 61, 98) 
        pdf.set_text_color(255, 255, 255)
        for i, h in enumerate(headers_text):
            pdf.cell(col_widths[i], 8, h, 1, 0, 'C', True)
        pdf.ln()
        
        # Table Rows
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(0, 0, 0)
        for idx, row in enumerate(data):
            # Alternating background
            if idx % 2 == 0: pdf.set_fill_color(245, 245, 245)
            else: pdf.set_fill_color(255, 255, 255)
            
            # State
            state_name = str(row.get('state', 'Unknown'))[:30]
            pdf.cell(col_widths[0], 7, state_name, 1, 0, 'L', True)
            
            # Risk/Vulnerability Score
            try: r_v = float(row.get('integrated_risk_score', 0))
            except: r_v = 0.0
            pdf.cell(col_widths[1], 7, f"{r_v:.1f}", 1, 0, 'C', True)
            
            # Coverage
            try: 
                bio_ratio = row.get('biometric_update_ratio')
                cov = float(bio_ratio) * 100 if bio_ratio else 0.0
            except: 
                cov = 0.0
            pdf.cell(col_widths[2], 7, f"{cov:.1f}%", 1, 0, 'C', True)
            
            # Category
            cat = str(row.get('service_risk_category', 'N/A'))[:20]
            pdf.cell(col_widths[3], 7, cat, 1, 0, 'C', True)
            
            # Rank
            pdf.cell(col_widths[4], 7, f"#{idx+1}", 1, 0, 'C', True)
            pdf.ln()
        
        # Generate binary content
        pdf_bytes = bytes(pdf.output())
        
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Regional_Analysis_{datetime.now().strftime('%Y%m%d')}.pdf",
                "Cache-Control": "no-cache"
            }
        )
    except Exception as e:
        import traceback
        error_msg = f"PDF Generation Failed: {str(e)}\n{traceback.format_exc()}"
        print(error_msg) # Log to console
        return jsonify({"error": f"Internal PDF Engine Error: {str(e)}"}), 500

# 3. Optimization Service Logic
@app.route('/api/optimization', methods=['POST'])
def run_optimization():
    if not validate_api_key():
        return unauthorized_response()
    
    try:
        from backend.budget_optimizer import maximize_inclusion
        data = request.json or {}
        budget = data.get('budget', 100000000) # Default 10Cr
        
        result = maximize_inclusion(budget)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 4. Social Service Logic
@app.route('/api/social/risk')
def get_social_risk():
    if not validate_api_key():
        return unauthorized_response()
    
    try:
        risk_path = os.path.join(DATA_DIR, 'integrated_service_risk.csv')
        features_path = os.path.join(DATA_DIR, 'social_vulnerability_features.csv')
        
        if not os.path.exists(risk_path):
            return jsonify({"error": "Risk data not found"}), 404
        
        data = []
        states_seen = set()
        numeric_cols = ['integrated_risk_score', 'biometric_update_ratio', 'social_vulnerability_index', 'growth_volatility']
        
        with open(risk_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                state = row.get('state')
                if state and state not in states_seen:
                    # Convert numeric columns to float
                    for key in numeric_cols:
                        if key in row and row[key]:
                            try: row[key] = float(row[key])
                            except: row[key] = 0.0
                        else:
                            row[key] = 0.0
                    data.append(row)
                    states_seen.add(state)
        
        if os.path.exists(features_path):
            features_map = {}
            with open(features_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('state'):
                        features_map[row['state']] = row.get('rural_population_percentage')
            for item in data:
                val = features_map.get(item['state'], 0.0)
                try:
                    item['rural_population_percentage'] = float(val) if val else 0.0
                except:
                    item['rural_population_percentage'] = 0.0

        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/social/fairness')
def get_social_fairness():
    if not validate_api_key():
        return unauthorized_response()
    
    try:
        path = os.path.join(DATA_DIR, 'social_fairness_analysis.csv')
        if not os.path.exists(path):
            return jsonify({"error": "Fairness data not found"}), 404
        
        data = []
        numeric_cols = [
            'social_vulnerability_index', 'biometric_update_ratio', 'fairness_gap', 
            'fairness_index', 'inclusion_priority_score', 'gender_parity_index', 
            'rural_parity_index', 'elderly_access_index', 'tribal_parity_index'
        ]
        
        with open(path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric columns to float for JS calculation safety
                for col in numeric_cols:
                    if col in row and row[col]:
                        try: row[col] = float(row[col])
                        except: row[col] = 0.0
                    else:
                        row[col] = 0.0
                data.append(row)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/social/insights')
def get_social_insights():
    if not validate_api_key():
        return unauthorized_response()
    
    try:
        path = os.path.join(DATA_DIR, 'social_insights.json')
        if not os.path.exists(path):
            return jsonify({"error": "Insights data not found"}), 404
        with open(path, 'r') as f: data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/anomaly/investigate/<state>')
def investigate_anomaly(state):
    if not validate_api_key():
        return unauthorized_response()
    
    try:
        with open(os.path.join(DATA_DIR, 'anomalies.json'), 'r') as f:
            data = json.load(f)
        
        target = None
        for category in ['critical_priority', 'medium_priority', 'low_risk']:
            for item in data.get(category, []):
                if item['state'].lower() == state.lower():
                    target = item
                    break
            if target: break
            
        if target:
            return jsonify({
                "state": state,
                "confidence_score": target.get('risk_score', 85.0),
                "root_cause": target.get('reason', 'Demographic shift correlation'),
                "recommended_action": "Targeted saturation drive (Module 7 protocol)",
                "historical_precedent": "Matches pattern seen in Bihar '22 refresh cycle",
                "ml_attribution": {
                    "synthetic_fraud_index": round(random.uniform(0.1, 0.4), 2),
                    "network_latency_distorted": False,
                    "biometric_drift": target.get('risk_score', 80) / 100
                }
            })
        return jsonify({"error": "No anomaly data found for this region"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 5. Admin & Governance Logic
@app.route('/api/admin/block', methods=['POST'])
def admin_block():
    if not validate_api_key():
        return unauthorized_response()
    
    data = request.json or {}
    entity_id = data.get('entity_id')
    
    # Simulate blocking logic (in a real app, update a database or watchlist.json)
    watchlist_path = os.path.join(DATA_DIR, 'watchlist_active.json')
    watchlist = {}
    if os.path.exists(watchlist_path):
        with open(watchlist_path, 'r') as f:
            watchlist = json.load(f)
    
    watchlist[entity_id] = {
        "status": "Blocked",
        "reason": data.get('reason'),
        "timestamp": datetime.now().isoformat()
    }
    
    with open(watchlist_path, 'w') as f:
        json.dump(watchlist, f, indent=4)
        
    return jsonify({"status": "Success", "message": f"Entity {entity_id} blocked."})

@app.route('/api/admin/undo', methods=['POST'])
def admin_undo():
    if not validate_api_key():
        return unauthorized_response()
    
    data = request.json or {}
    entity_id = data.get('entity_id')
    
    watchlist_path = os.path.join(DATA_DIR, 'watchlist_active.json')
    if os.path.exists(watchlist_path):
        with open(watchlist_path, 'r') as f:
            watchlist = json.load(f)
        if entity_id in watchlist:
            del watchlist[entity_id]
            with open(watchlist_path, 'w') as f:
                json.dump(watchlist, f, indent=4)
                
    return jsonify({"status": "Success", "message": f"Block for {entity_id} reversed."})

@app.route('/api/admin/download-audit')
def download_audit():
    if not validate_api_key():
        return unauthorized_response()
    
    # Return a dummy audit trail CSV or PDF
    content = "Timestamp,Entity,Action,Reason,ML_Confidence\n"
    content += f"{datetime.now().isoformat()},System,AuditInitiated,SelfCheck,100%\n"
    
    return Response(
        content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=ALRIS_Audit_Trail.csv"}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=int(os.environ.get('PORT', 5000)))
