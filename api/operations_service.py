from flask import Flask, jsonify, send_file
import os
import csv
from datetime import datetime
from api.common import DATA_DIR, require_api_key

app = Flask(__name__)

@app.route('/api/social/export/csv')
@require_api_key
def export_social_risk_csv():
    """Exports the integrated social risk data as CSV."""
    try:
        path = os.path.join(DATA_DIR, 'integrated_service_risk.csv')
        if os.path.exists(path):
            return send_file(path, as_attachment=True, download_name=f"Regional_Analysis_{datetime.now().strftime('%Y%m%d')}.csv")
        return jsonify({"error": "Risk data not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/social/export/pdf')
@require_api_key
def export_social_risk_pdf():
    """Exports the integrated social risk data as a formatted PDF report."""
    try:
        from fpdf import FPDF
        
        path = os.path.join(DATA_DIR, 'integrated_service_risk.csv')
        
        if os.path.exists(path):
            data = []
            states_seen = set()
            with open(path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    state = row.get('state')
                    if state and state not in states_seen:
                        data.append(row)
                        states_seen.add(state)
            
            # Sort by risk score
            def get_risk(x):
                try: return float(x.get('integrated_risk_score', 0))
                except: return 0.0
            data.sort(key=get_risk, reverse=True)
            
            # Create PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, 'UIDAI - Regional Classification Analysis Report', 0, 1, 'C')
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")}', 0, 1, 'C')
            pdf.ln(5)
            
            # Table Header
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(0, 61, 98)  # NIC Blue
            pdf.set_text_color(255, 255, 255)
            col_widths = [60, 35, 30, 45, 20]
            headers = ['State / UT', 'Vuln. Score', 'Coverage %', 'Risk Category', 'Rank']
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 8, header, 1, 0, 'C', True)
            pdf.ln()
            
            # Table Data
            pdf.set_font('Arial', '', 8)
            pdf.set_text_color(0, 0, 0)
            for idx, row in enumerate(data):
                if idx % 2 == 0:
                    pdf.set_fill_color(245, 245, 245)
                else:
                    pdf.set_fill_color(255, 255, 255)
                
                pdf.cell(col_widths[0], 7, str(row['state'])[:30], 1, 0, 'L', True)
                try: risk_val = float(row['integrated_risk_score'])
                except: risk_val = 0.0
                pdf.cell(col_widths[1], 7, f"{risk_val:.1f}", 1, 0, 'C', True)
                try: coverage = float(row.get('biometric_update_ratio', 0)) * 100
                except: coverage = 0.0
                pdf.cell(col_widths[2], 7, f"{coverage:.1f}%", 1, 0, 'C', True)
                pdf.cell(col_widths[3], 7, str(row['service_risk_category'])[:20], 1, 0, 'C', True)
                pdf.cell(col_widths[4], 7, f"#{idx+1}", 1, 0, 'C', True)
                pdf.ln()
            
            # Footer
            pdf.ln(10)
            pdf.set_font('Arial', 'I', 8)
            pdf.cell(0, 10, 'Confidential - For Official Use Only | UIDAI FPEWS Dashboard', 0, 1, 'C')
            
            # Save PDF (Temporary path for download)
            pdf_path = os.path.join(DATA_DIR, 'Regional_Classification_Analysis.pdf')
            pdf.output(pdf_path)
            
            return send_file(pdf_path, as_attachment=True, download_name=f"Regional_Analysis_{datetime.now().strftime('%Y%m%d')}.pdf")
        return jsonify({"error": "Risk data not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
